# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Baseline JSON-RPC 2.0 communication protocol over stdio."""

from __future__ import annotations

import json
import os
import select
import sys
import time
import traceback
from pathlib import Path
from typing import Any, BinaryIO, TypedDict, cast

from zenzic.core.adapters import BaseAdapter, get_adapter
from zenzic.core.discovery import iter_markdown_sources
from zenzic.core.exclusion import LayeredExclusionManager
from zenzic.core.rules import AdaptiveRuleEngine, RuleFinding
from zenzic.core.scanner import _build_rule_engine
from zenzic.lsp.documents import DocumentManager
from zenzic.models.config import ZenzicConfig
from zenzic.models.diagnostics import (
    DiagnosticPosition,
    DiagnosticRange,
    Severity,
    ZenzicDiagnostic,
)
from zenzic.models.vsm import Route, VirtualBufferOverlay, VirtualSiteMap, build_vsm


class JsonRpcMessage(TypedDict, total=False):
    """PEP 484 TypedDict for JSON-RPC 2.0 message validation."""

    jsonrpc: str
    id: int | str
    method: str
    params: dict[str, Any]


class LanguageServer:
    """Dependency-free JSON-RPC 2.0 dispatcher over raw byte streams."""

    def __init__(self, stdin: BinaryIO | None = None, stdout: BinaryIO | None = None) -> None:
        """Initialize the server with specific or default byte streams."""
        self.stdin = stdin or sys.stdin.buffer
        self.stdout = stdout or sys.stdout.buffer
        self.shutdown_received = False
        self.exit_received = False
        self.exit_code = 0
        self.documents = DocumentManager()

        # Phase 2: Diagnostic Engine
        self.config: ZenzicConfig | None = None
        self.rule_engine: AdaptiveRuleEngine | None = None

        # Phase 3: Debounce
        self.dirty_documents: dict[str, float] = {}

        # Phase 4: VSM Integration
        self.repo_root: Path | None = None
        self.adapter: BaseAdapter | None = None
        self.vsm: VirtualSiteMap | None = None
        self.overlay: VirtualBufferOverlay | None = None

    def send_message(self, message: dict[str, Any]) -> None:
        """Encode and send a JSON-RPC message to stdout."""
        body = json.dumps(message, separators=(",", ":")).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\nContent-Type: application/vscode-jsonrpc; charset=utf-8\r\n\r\n".encode(
            "ascii"
        )
        self.stdout.write(header + body)
        self.stdout.flush()

    def send_error(self, request_id: int | str | None, code: int, message: str) -> None:
        """Send a JSON-RPC error response."""
        response: dict[str, Any] = {"jsonrpc": "2.0", "error": {"code": code, "message": message}}
        if request_id is not None:
            response["id"] = request_id
        self.send_message(response)

    def send_response(
        self,
        request_id: int | str,
        result: dict[str, Any] | None = None,
        error: dict[str, Any] | None = None,
    ) -> None:
        """Send a JSON-RPC response."""
        response: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id}
        if error is not None:
            response["error"] = error
        else:
            response["result"] = result
        self.send_message(response)

    def serve(self) -> None:
        """Run the main synchronous event loop with debounce multiplexing."""
        import io

        buffer = bytearray()

        while not self.exit_received:
            try:
                # 1. Process Debounced Dirty Documents
                self._flush_dirty_documents()

                # 2. Yield and wait for input
                try:
                    rlist, _, _ = select.select([self.stdin], [], [], 0.1)
                except (ValueError, OSError, io.UnsupportedOperation, AttributeError):
                    # Mock testing stream fallback
                    rlist = [self.stdin]

                if not rlist:
                    continue

                # 3. Fast non-blocking chunk ingestion
                try:
                    fd = self.stdin.fileno()
                    chunk = os.read(fd, 8192)
                except Exception:
                    chunk = self.stdin.read(8192)

                if not chunk:
                    self.exit_received = True
                    break

                buffer.extend(chunk)

                # 4. Extract and route fully buffered messages
                while True:
                    header_end = buffer.find(b"\r\n\r\n")
                    if header_end == -1:
                        break

                    header_data = buffer[:header_end]
                    content_length = 0
                    for line in header_data.split(b"\r\n"):
                        if b":" in line:
                            key, val = line.split(b":", 1)
                            if key.decode("ascii").strip().lower() == "content-length":
                                content_length = int(val.decode("ascii").strip())

                    msg_start = header_end + 4
                    if len(buffer) < msg_start + content_length:
                        break

                    body = buffer[msg_start : msg_start + content_length]
                    buffer = buffer[msg_start + content_length :]

                    try:
                        raw_msg = json.loads(body.decode("utf-8"))
                    except json.JSONDecodeError as e:
                        self.send_error(None, -32700, f"Parse error: {e}")
                        continue

                    message = cast(JsonRpcMessage, raw_msg)
                    if message.get("jsonrpc") != "2.0":
                        self.send_error(
                            message.get("id"),
                            -32600,
                            "Invalid Request: missing or invalid jsonrpc version",
                        )
                        continue

                    self.handle_message(message)

            except Exception as e:
                sys.stderr.write(f"ZLS Error: {e}\n{traceback.format_exc()}\n")
                sys.stderr.flush()

        # Emit any remaining dirty documents on clean exit
        self._flush_dirty_documents(force=True)

    def _flush_dirty_documents(self, force: bool = False) -> None:
        """Collect expired dirty URIs and trigger incremental validation."""
        now = time.time()
        incremental_uris: set[str] = set()
        for uri, ts in list(self.dirty_documents.items()):
            if force or now - ts >= 0.3:
                incremental_uris.add(uri)
                del self.dirty_documents[uri]
        if incremental_uris:
            self._sync_workspace_and_publish(incremental_uris)

    def _build_vsm_sync(self) -> None:
        """Synchronously build the initial VSM."""
        if not self.repo_root:
            return

        if not self.config:
            self.config, _ = ZenzicConfig.load(self.repo_root)

        if not self.rule_engine:
            self.rule_engine = _build_rule_engine(self.config)

        docs_root = self.repo_root / self.config.docs_dir
        exclusion_mgr = LayeredExclusionManager(
            self.config, repo_root=self.repo_root, docs_root=docs_root
        )

        md_contents: dict[Path, str] = {}
        for md_file in iter_markdown_sources(docs_root, self.config, exclusion_mgr):
            try:
                md_contents[md_file.resolve()] = md_file.read_text(encoding="utf-8")
            except OSError:
                continue

        self.adapter = get_adapter(self.config.build_context, docs_root, self.repo_root)
        self.vsm = build_vsm(self.adapter, docs_root, md_contents, repo_root=self.repo_root)
        assert self.vsm is not None
        self.overlay = VirtualBufferOverlay(self.vsm)
        # Populate overlay with currently open documents
        for uri, text in self.documents.documents.items():
            self.overlay.update(uri, text)
        self._flush_dirty_documents()

    def _handle_file_changes(self, changes: list[dict[str, Any]]) -> None:
        """Incrementally update the VSM in O(1) time."""
        if self.vsm is None or not self.adapter or not self.config:
            return

        assert isinstance(self.vsm, VirtualSiteMap)

        from zenzic.core.validator import anchors_in_file

        for change in changes:
            uri = change.get("uri", "")
            change_type = change.get("type")
            if not uri.startswith("file://"):
                continue
            file_path = Path(uri[7:]).resolve()

            if change_type in (1, 2):  # Created or Changed
                try:
                    text = file_path.read_text(encoding="utf-8")
                    if not hasattr(self, "md_contents_cache"):
                        self.md_contents_cache = {}
                    if not hasattr(self, "anchors_cache"):
                        self.anchors_cache = {}
                    self.md_contents_cache[file_path] = text
                    self.anchors_cache[file_path] = anchors_in_file(text)
                except OSError:
                    pass
            elif change_type == 3:  # Deleted
                if hasattr(self, "md_contents_cache"):
                    self.md_contents_cache.pop(file_path, None)
                if hasattr(self, "anchors_cache"):
                    self.anchors_cache.pop(file_path, None)

            self.dirty_documents[uri] = 0.0

        for open_uri in self.documents.documents:
            self.dirty_documents[open_uri] = 0.0
        self._flush_dirty_documents()

    def handle_message(self, message: JsonRpcMessage) -> None:
        """Dispatch a single JSON-RPC message to the correct handler."""
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")

        if not method:
            self.send_error(msg_id, -32600, "Invalid Request: missing method")
            return

        if method == "initialize":
            assert msg_id is not None
            root_uri = params.get("rootUri")
            if root_uri and root_uri.startswith("file://"):
                self.repo_root = Path(root_uri[7:])
            elif params.get("workspaceFolders"):
                first_ws = params["workspaceFolders"][0]
                if first_ws.get("uri", "").startswith("file://"):
                    self.repo_root = Path(first_ws["uri"][7:])

            self.send_response(
                msg_id,
                result={
                    "capabilities": {
                        "textDocumentSync": 2,  # Incremental sync (Zero-DBT Enforcement)
                        "hoverProvider": True,
                    },
                    "serverInfo": {"name": "Zenzic Language Server", "version": "0.21.0"},
                },
            )

            # Eagerly initialize configuration and engine on 'initialize'
            if self.repo_root and not self.config:
                self.config, _ = ZenzicConfig.load(self.repo_root)
                self.rule_engine = _build_rule_engine(self.config)

        elif method == "initialized":
            if self.repo_root:
                self.send_message(
                    {
                        "jsonrpc": "2.0",
                        "id": "watch-md",
                        "method": "client/registerCapability",
                        "params": {
                            "registrations": [
                                {
                                    "id": "watch-md",
                                    "method": "workspace/didChangeWatchedFiles",
                                    "registerOptions": {"watchers": [{"globPattern": "**/*.md"}]},
                                }
                            ]
                        },
                    }
                )
                self._build_vsm_sync()
        elif method == "workspace/didChangeWatchedFiles":
            self._handle_file_changes(params.get("changes", []))
        elif method == "shutdown":
            self.shutdown_received = True
            if msg_id is not None:
                self.send_response(msg_id, result=None)
        elif method == "exit":
            self.exit_received = True
            self.exit_code = 0 if self.shutdown_received else 1
        elif method == "textDocument/didOpen":
            self.documents.did_open(params)
            uri = params.get("textDocument", {}).get("uri", "")
            if uri in self.documents.documents:
                if self.overlay:
                    self.overlay.update(uri, self.documents.documents[uri])
                self.dirty_documents[uri] = time.time()
        elif method == "textDocument/didChange":
            self.documents.did_change(params)
            uri = params.get("textDocument", {}).get("uri", "")
            if uri in self.documents.documents:
                if self.overlay:
                    self.overlay.update(uri, self.documents.documents[uri])
                self.dirty_documents[uri] = time.time()
        elif method == "textDocument/didClose":
            # Memory Hygiene: purge the document state entirely
            pass

    def _sync_workspace_and_publish(self, incremental_uris: set[str] | None = None) -> None:
        """Run validation incrementally. Full sync on first run, partial otherwise.

        Topology awareness (reverse index) is owned by the VirtualSiteMap.
        """
        has_workspace = self.repo_root is not None
        repo_root = self.repo_root or Path("/")

        if not self.config:
            if self.repo_root:
                self.config, _ = ZenzicConfig.load(self.repo_root)
            else:
                self.config = ZenzicConfig()
        if not self.rule_engine:
            self.rule_engine = _build_rule_engine(self.config)

        docs_root = repo_root / self.config.docs_dir if self.repo_root else Path("/_zenzic_virtual")

        if not self.adapter:
            self.adapter = get_adapter(self.config.build_context, docs_root, repo_root)
            if self.vsm is None:
                self.vsm = VirtualSiteMap()

            assert isinstance(self.vsm, VirtualSiteMap)

            if self.overlay is None:
                self.overlay = VirtualBufferOverlay(self.vsm)
                for open_uri, open_text in self.documents.documents.items():
                    self.overlay.update(open_uri, open_text)

        assert isinstance(self.vsm, VirtualSiteMap)

        # Initialize per-file content cache if first run (not topology state)
        if not hasattr(self, "md_contents_cache"):
            self.md_contents_cache = {}
            self.anchors_cache = {}
            incremental_uris = None  # Force full sync

        from zenzic.core.discovery import iter_markdown_sources
        from zenzic.core.exclusion import LayeredExclusionManager
        from zenzic.core.rules import ResolutionContext
        from zenzic.core.validator import anchors_in_file
        from zenzic.models.vsm import build_vsm

        exclusion_manager = LayeredExclusionManager(
            self.config, repo_root=repo_root, docs_root=docs_root
        )

        # 1. Update text and anchors for modified files (or all files on full sync)
        files_to_process: set[Path] = set()

        if incremental_uris is None:
            # Full read
            if has_workspace:
                for md_file in iter_markdown_sources(docs_root, self.config, exclusion_manager):
                    uri = f"file://{md_file.resolve()}"
                    if self.overlay and uri in self.overlay.buffers:
                        text = self.overlay.buffers[uri]
                    else:
                        try:
                            text = md_file.read_text(encoding="utf-8")
                        except OSError:
                            continue
                    path = md_file.resolve()
                    self.md_contents_cache[path] = text
                    self.anchors_cache[path] = anchors_in_file(text)
                    files_to_process.add(path)

            # Open buffers that might be outside docs_root or not on disk yet
            for uri in self.documents.documents:
                if uri.startswith("file://"):
                    path = Path(uri[7:]).resolve()
                    if path not in self.md_contents_cache:
                        if self.overlay and uri in self.overlay.buffers:
                            text = self.overlay.buffers[uri]
                            self.md_contents_cache[path] = text
                            self.anchors_cache[path] = anchors_in_file(text)
                            files_to_process.add(path)
        else:
            # Incremental read
            for uri in incremental_uris:
                if not uri.startswith("file://"):
                    continue
                path = Path(uri[7:]).resolve()
                if self.overlay and uri in self.overlay.buffers:
                    text = self.overlay.buffers[uri]
                    self.md_contents_cache[path] = text
                    self.anchors_cache[path] = anchors_in_file(text)
                files_to_process.add(path)

        # 2. Re-build VSM topology
        if incremental_uris is None:
            self.vsm = build_vsm(
                self.adapter,
                docs_root,
                self.md_contents_cache,
                anchors_cache=self.anchors_cache,
                repo_root=repo_root,
            )
        else:
            # O(K) in-place patch
            for path in files_to_process:
                # 1. If file is deleted, remove route from self.vsm
                if path not in self.md_contents_cache:
                    try:
                        if path.is_relative_to(docs_root):
                            rel_obj = path.relative_to(docs_root)
                        else:
                            rel_obj = path
                        route_meta = self.adapter.get_route_info(rel_obj)
                        canonical = route_meta.canonical_url
                    except Exception:
                        canonical = ""
                    if canonical and canonical in self.vsm:
                        del self.vsm[canonical]
                    if hasattr(self.vsm, "remove_outgoing_links"):
                        self.vsm.remove_outgoing_links(path)
                else:
                    # 2. If created or modified, update route in self.vsm
                    try:
                        if path.is_relative_to(docs_root):
                            rel_obj = path.relative_to(docs_root)
                        else:
                            rel_obj = path
                        route_meta = self.adapter.get_route_info(rel_obj)
                    except Exception:
                        route_meta = None

                    if route_meta:
                        self.vsm[route_meta.canonical_url] = Route(
                            url=route_meta.canonical_url,
                            source=rel_obj.as_posix(),
                            status=route_meta.status,
                            anchors=self.anchors_cache.get(path, set()),
                        )
                    if hasattr(self.vsm, "reindex_outgoing_links"):
                        self.vsm.reindex_outgoing_links(
                            path,
                            self.md_contents_cache[path],
                            docs_root,
                            [],
                            self.adapter,
                        )

        assert isinstance(self.vsm, VirtualSiteMap)

        if self.overlay is not None:
            self.overlay.vsm = self.vsm

        # 3. Expand files_to_process with dependents via VSM's O(1) reverse index
        if incremental_uris is not None:
            dependents: set[Path] = set()
            for path in files_to_process:
                # 1. Look up canonical URL via relative path in the VSM
                try:
                    rel_posix = path.relative_to(docs_root).as_posix()
                except ValueError:
                    rel_posix = path.absolute().as_posix()
                canonical = next((url for url, r in self.vsm.items() if r.source == rel_posix), "")

                # 2. Or compute it directly via adapter.get_route_info
                if not canonical:
                    try:
                        if path.is_relative_to(docs_root):
                            rel_obj = path.relative_to(docs_root)
                        else:
                            rel_obj = path
                        meta = self.adapter.get_route_info(rel_obj)
                        canonical = meta.canonical_url
                    except Exception:
                        pass

                if canonical and hasattr(self.vsm, "incoming_links"):
                    dependents.update(self.vsm.incoming_links.get(canonical, set()))
            files_to_process.update(dependents)

        # 4. Add virtual routes for out-of-bounds files in files_to_process (Mirror Law)
        for path in files_to_process:
            try:
                rel_posix = path.relative_to(docs_root).as_posix()
            except ValueError:
                rel_posix = path.absolute().as_posix()

            # Find if there is already a route for this source
            route = next((r for r in self.vsm.values() if r.source == rel_posix), None)
            if not route:
                virtual_url = f"/_virtual/{path.name}"
                self.vsm[virtual_url] = Route(
                    url=virtual_url,
                    source=rel_posix,
                    status="REACHABLE",
                    anchors=self.anchors_cache.get(path, set()),
                )

        # 5. Run URP & Engine ONLY on files_to_process
        engine = self.rule_engine
        assert engine is not None
        for path in files_to_process:
            if path not in self.md_contents_cache:
                continue
            text = self.md_contents_cache[path]
            uri = f"file://{path}"
            findings: list[RuleFinding] = []

            from zenzic.core.suppressions import SuppressionTracker

            tracker = SuppressionTracker(path, text)

            # Atomic Rules
            findings.extend(engine.run_with_tracker(path, text, tracker))

            # VSM-aware Rules
            context = ResolutionContext(docs_root=docs_root, source_file=path)
            findings.extend(engine.run_vsm(path, text, self.vsm, self.anchors_cache, context))

            # Snippets
            from zenzic.core.validator import check_snippet_content

            for s_err in check_snippet_content(text, path, self.config):
                from zenzic.core.rules import RuleFinding

                findings.append(
                    RuleFinding(
                        file_path=path,
                        line_no=s_err.line_no,
                        rule_id=s_err.code,
                        message=s_err.message,
                        severity="error",
                    )
                )

            # URP In-Memory Checks (Z120-Z124, Z205, Z102, Z105, Z202, Z203)
            # Extracted from the previous URP logic to run incrementally per file
            urp_findings = self._run_incremental_urp(path, text, docs_root)
            findings.extend(urp_findings)

            findings.extend(tracker.get_dead_suppressions())

            # Convert findings to strictly typed ZenzicDiagnostic instances
            typed_diags: list[ZenzicDiagnostic] = []
            for f in findings:
                line_no = max(0, f.line_no - 1)
                lines = text.splitlines()
                matched_line = lines[line_no] if 0 <= line_no < len(lines) else ""

                col_start = getattr(f, "col_start", 0)
                match_text = getattr(f, "match_text", "")
                match_len = len(match_text) if match_text else len(matched_line)

                utf16_start = self._to_utf16_col(matched_line, col_start)
                utf16_end = self._to_utf16_col(matched_line, col_start + match_len)

                severity_str = getattr(f, "severity", "error")
                severity = {
                    "error": Severity.ERROR,
                    "warning": Severity.WARNING,
                    "info": Severity.INFORMATION,
                }.get(severity_str, Severity.ERROR)

                typed_diags.append(
                    ZenzicDiagnostic(
                        range=DiagnosticRange(
                            start=DiagnosticPosition(line=line_no, character=utf16_start),
                            end=DiagnosticPosition(line=line_no, character=utf16_end),
                        ),
                        severity=severity,
                        code=getattr(f, "rule_id", "Unknown"),
                        source="zenzic",
                        message=getattr(f, "message", "Violation"),
                    )
                )

            # Store strictly typed diagnostics on the VSM route (Mirror Law)
            try:
                rel = path.relative_to(docs_root).as_posix()
            except ValueError:
                rel = path.absolute().as_posix()
            for route in self.vsm.values():
                if route.source == rel:
                    route.diagnostics = typed_diags
                    break

        # 6. Serialize at transport boundary and publish
        for path in files_to_process:
            uri = f"file://{path}"
            try:
                rel = path.relative_to(docs_root).as_posix()
            except ValueError:
                rel = path.absolute().as_posix()
            typed_diags = next(
                (r.diagnostics for r in self.vsm.values() if r.source == rel),
                [],
            )
            # to_lsp_dict() is the ONLY serialization site in the codebase
            self.send_message(
                {
                    "jsonrpc": "2.0",
                    "method": "textDocument/publishDiagnostics",
                    "params": {
                        "uri": uri,
                        "diagnostics": [d.to_lsp_dict() for d in typed_diags],
                    },
                }
            )

    def _run_incremental_urp(self, path: Path, text: str, docs_root: Path) -> list[RuleFinding]:
        """Run the URP checks on a single file using the cached graph topology."""
        from urllib.parse import urlsplit

        from zenzic.core.rules import RuleFinding, _extract_inline_links_with_lines
        from zenzic.core.validator import PolyglotExtractor

        assert isinstance(self.vsm, VirtualSiteMap)

        findings = []
        lines = text.splitlines()

        def _source_line(lineno: int) -> str:
            idx = lineno - 1
            return lines[idx].strip() if 0 <= idx < len(lines) else ""

        # Polyglot Extractor
        for node in PolyglotExtractor().extract(text):
            ctx = _source_line(node.line_no)
            if node.z205_scheme:
                findings.append(
                    RuleFinding(
                        path,
                        node.line_no,
                        "Z205",
                        f"forbidden scheme '{node.z205_scheme}' detected",
                        severity="error",
                        matched_line=ctx,
                        col_start=0,
                        match_text=node.raw_tag,
                    )
                )
            for attr in node.blacklisted_attrs:
                findings.append(
                    RuleFinding(
                        path,
                        node.line_no,
                        "Z124",
                        f"opaque attribute '{attr}' detected",
                        severity="error",
                        matched_line=ctx,
                        col_start=0,
                        match_text=node.raw_tag,
                    )
                )
            if node.is_missing_href:
                findings.append(
                    RuleFinding(
                        path,
                        node.line_no,
                        "Z121",
                        "missing href or src",
                        severity="error",
                        matched_line=ctx,
                        col_start=0,
                        match_text=node.raw_tag,
                    )
                )
            if node.is_jump_link:
                findings.append(
                    RuleFinding(
                        path,
                        node.line_no,
                        "Z122",
                        "href='#' detected",
                        severity="error",
                        matched_line=ctx,
                        col_start=0,
                        match_text=node.raw_tag,
                    )
                )
            for attr in node.unknown_attrs:
                findings.append(
                    RuleFinding(
                        path,
                        node.line_no,
                        "Z120",
                        f"unknown attribute '{attr}'",
                        severity="error",
                        matched_line=ctx,
                        col_start=0,
                        match_text=node.raw_tag,
                    )
                )
            if node.info_scheme:
                findings.append(
                    RuleFinding(
                        path,
                        node.line_no,
                        "Z123",
                        f"non-HTTP scheme '{node.info_scheme}'",
                        severity="info",
                        matched_line=ctx,
                        col_start=0,
                        match_text=node.raw_tag,
                    )
                )

        # Markdown Links
        local_anchors = self.anchors_cache.get(path, set())
        _bypass_schemes = (
            "mailto:",
            "tel:",
            "javascript:",
            "data:",
            "irc:",
            "xmpp:",
            "http://",
            "https://",
        )

        for url, lineno, raw_line in _extract_inline_links_with_lines(text):
            if url.startswith(_bypass_schemes) or url == "#":
                continue

            parsed = urlsplit(url)

            # Z202 / Z203
            if "../" in url and url.count("../") > len(path.parents):
                from zenzic.core.validator import _classify_traversal_intent

                _intent = _classify_traversal_intent(url)
                findings.append(
                    RuleFinding(
                        path,
                        lineno,
                        "Z203" if _intent == "suspicious" else "Z202",
                        f"Path traversal escape detected: '{url}'",
                        severity="error",
                        matched_line=raw_line,
                    )
                )
                continue

            # Z105 / Z203
            elif parsed.path.startswith("/"):
                from zenzic.core.validator import _classify_traversal_intent

                _intent = _classify_traversal_intent(url)
                if _intent == "suspicious":
                    findings.append(
                        RuleFinding(
                            path,
                            lineno,
                            "Z203",
                            f"Path traversal targeting OS system directories: '{url}'",
                            severity="error",
                            matched_line=raw_line,
                        )
                    )
                else:
                    findings.append(
                        RuleFinding(
                            path,
                            lineno,
                            "Z105",
                            f"Absolute path '{url}' found.",
                            severity="error",
                            matched_line=raw_line,
                        )
                    )
                continue

            # Z102 (Local and Cross-file)
            if parsed.fragment:
                anchor = parsed.fragment.lower()
                if not parsed.path:
                    if anchor not in local_anchors:
                        findings.append(
                            RuleFinding(
                                path,
                                lineno,
                                "Z102",
                                f"anchor '#{anchor}' not found",
                                severity="error",
                                matched_line=raw_line,
                            )
                        )
                else:
                    from urllib.parse import unquote

                    target_path = (path.parent / unquote(parsed.path)).resolve()
                    try:
                        if target_path.is_relative_to(docs_root):
                            rel_obj = target_path.relative_to(docs_root)
                        else:
                            rel_obj = target_path
                        if self.adapter:
                            route_meta = self.adapter.get_route_info(rel_obj)
                            route = self.vsm.get(route_meta.canonical_url)
                        else:
                            route = None
                    except Exception:
                        route = None

                    if route is not None and anchor not in route.anchors:
                        findings.append(
                            RuleFinding(
                                path,
                                lineno,
                                "Z102",
                                f"anchor '#{anchor}' not found in '{parsed.path}'",
                                severity="error",
                                matched_line=raw_line,
                            )
                        )

        return findings

    def _handle_hover(self, params: dict[str, Any], msg_id: int | str | None) -> None:
        if msg_id is None or self.vsm is None or not self.repo_root or not self.config:
            return

        assert isinstance(self.vsm, VirtualSiteMap)

        doc = params.get("textDocument", {})
        uri = doc.get("uri", "")
        pos = params.get("position", {})
        line = pos.get("line", 0)
        char = pos.get("character", 0)

        docs_root = self.repo_root / self.config.docs_dir
        try:
            rel = Path(uri[7:]).relative_to(docs_root).as_posix()
        except ValueError:
            self.send_response(msg_id, result=None)
            return

        target_route = None
        for route in self.vsm.values():
            if route.source == rel:
                target_route = route
                break

        if not target_route:
            self.send_response(msg_id, result=None)
            return

        matched: ZenzicDiagnostic | None = None
        for d in target_route.diagnostics:
            s_line = d.range.start.line
            e_line = d.range.end.line
            if s_line <= line <= e_line:
                if s_line == line and char < d.range.start.character:
                    continue
                if e_line == line and char > d.range.end.character:
                    continue
                matched = d
                break

        if not matched:
            self.send_response(msg_id, result=None)
            return

        code = matched.code
        from zenzic.core.codes import CODE_DEFINITIONS, CODE_DESCRIPTIONS

        defn = CODE_DEFINITIONS.get(code)
        desc = CODE_DESCRIPTIONS.get(code, "No remediation guidance available.")

        contents: list[str] = []
        if defn:
            contents.append(
                f"**{code}** (Penalty: -{defn.penalty} pts, Category: {defn.category or 'ungraded'})"
            )
        else:
            contents.append(f"**{code}**")
        contents.append(desc)

        self.send_response(
            msg_id,
            result={"contents": {"kind": "markdown", "value": "\n\n".join(contents)}},
        )

    def _to_utf16_col(self, line: str, py_idx: int) -> int:
        """Convert a Python string index into a UTF-16 code unit offset."""
        col = 0
        for i, c in enumerate(line):
            if i >= py_idx:
                break
            col += 2 if ord(c) > 0xFFFF else 1
        return col
