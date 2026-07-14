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

from zenzic.core.adapters import get_adapter
from zenzic.core.discovery import iter_markdown_sources
from zenzic.core.exclusion import LayeredExclusionManager
from zenzic.core.rules import AdaptiveRuleEngine, ResolutionContext, RuleFinding
from zenzic.core.scanner import _build_rule_engine
from zenzic.lsp.documents import DocumentManager
from zenzic.models.config import ZenzicConfig
from zenzic.models.vsm import VSM, Route, build_vsm


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
        self.adapter: Any | None = None
        self.vsm: VSM | None = None

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
                now = time.time()
                for uri, last_edit in list(self.dirty_documents.items()):
                    if now - last_edit >= 0.3:
                        self._publish_diagnostics(uri, self.documents.documents[uri])
                        del self.dirty_documents[uri]

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
        """Push diagnostics if debounce interval has elapsed."""
        now = time.time()
        for uri, ts in list(self.dirty_documents.items()):
            if force or now - ts >= 0.3:
                self._publish_diagnostics(uri, self.documents.documents[uri])
                del self.dirty_documents[uri]

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
        self._flush_dirty_documents()

    def _handle_file_changes(self, changes: list[dict[str, Any]]) -> None:
        """Incrementally update the VSM in O(1) time."""
        if not self.vsm or not self.adapter or not self.config or not self.repo_root:
            return

        docs_root = self.repo_root / self.config.docs_dir

        for change in changes:
            uri = change.get("uri", "")
            change_type = change.get("type")
            if not uri.startswith("file://"):
                continue
            file_path = Path(uri[7:])

            try:
                rel_path_obj = file_path.relative_to(docs_root)
                rel_path_str = rel_path_obj.as_posix()
            except ValueError:
                continue

            if change_type in (1, 2):  # Created or Changed
                route_meta = self.adapter.get_route_info(rel_path_obj)
                if route_meta:
                    self.vsm[route_meta.canonical_url] = Route(
                        url=route_meta.canonical_url,
                        source=rel_path_str,
                        status=route_meta.status,
                    )
            elif change_type == 3:  # Deleted
                urls_to_remove = [url for url, r in self.vsm.items() if r.source == rel_path_str]
                for u in urls_to_remove:
                    del self.vsm[u]

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
                        "textDocumentSync": 2  # Incremental sync (Zero-DBT Enforcement)
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
                self.dirty_documents[uri] = time.time()
        elif method == "textDocument/didChange":
            self.documents.did_change(params)
            uri = params.get("textDocument", {}).get("uri", "")
            if uri in self.documents.documents:
                self.dirty_documents[uri] = time.time()
        elif method == "textDocument/didClose":
            # Memory Hygiene: purge the document state entirely
            self.documents.did_close(params)

    def _publish_diagnostics(self, uri: str, text: str) -> None:
        """Run the rule engine on the in-memory document state and publish diagnostics.

        Diagnostic sources (all pure / zero disk-I/O for the current document):

        1. ``rule_engine.run()``  — built-in rules: Z108, Z201, Z505, Z107, Z506, Z601 …
        2. ``rule_engine.run_vsm()`` — VSM-aware rules: Z101 (broken cross-file link)
        3. ``validate_single_document_urp()`` — Decoupled URP: PolyglotExtractor (Z120-124, Z205), same-page anchors (Z102), absolute paths (Z105)
        4. ``check_snippet_content()`` — Z503: malformed code snippets
        """

        if uri.startswith("file://"):
            file_path = Path(uri[7:])
        else:
            file_path = Path(uri)

        # Ensure fallback for zero-config instances
        if not self.config:
            self.config = ZenzicConfig()
        if not self.rule_engine:
            self.rule_engine = _build_rule_engine(self.config)

        # ── 1. Core rule engine (Z108, Z201, Z505, Z107, Z506, …) ─────────────
        findings = self.rule_engine.run(file_path, text) if self.rule_engine else []

        # ── 2. VSM-aware rules (Z101 — broken cross-file link) ────────────────
        if self.vsm is not None and self.config is not None and self.repo_root is not None:
            assert self.rule_engine is not None
            docs_root = self.repo_root / self.config.docs_dir
            context = ResolutionContext(docs_root=docs_root, source_file=file_path)
            vsm_findings = self.rule_engine.run_vsm(
                file_path=file_path, text=text, vsm=self.vsm, anchors_cache={}, context=context
            )
            findings.extend(vsm_findings)

        # ── 3. URP (Uniform Resolver Pipeline) - In-Memory Validation (Z102, Z120-Z124, Z205, Z105)
        from zenzic.core.validator import validate_single_document_urp
        
        urp_errors = validate_single_document_urp(
            content=text,
            file_path=file_path,
            vsm=self.vsm or {},
            config=self.config
        )
        
        for err in urp_errors:
            findings.append(
                RuleFinding(
                    file_path=err.file_path,
                    line_no=err.line_no,
                    rule_id=err.error_type,
                    message=err.message,
                    severity="error" if err.error_type != "Z123" else "info",
                    matched_line=err.source_line,
                    col_start=err.col_start,
                    match_text=err.match_text,
                )
            )

        # ── 5. Snippet syntax validation (Z503) ───────────────────────────────
        from zenzic.core.validator import check_snippet_content

        snippet_errors = check_snippet_content(text, file_path, ZenzicConfig())

        diagnostics = []
        for f in findings:
            # LSP line is 0-indexed, Zenzic line_no is 1-indexed
            line_no = max(0, f.line_no - 1)

            col_start = getattr(f, "col_start", 0)
            match_text = getattr(f, "match_text", "")
            col_end = col_start + len(match_text) if match_text else col_start

            matched_line = getattr(f, "matched_line", "") or ""

            utf16_start = self._to_utf16_col(matched_line, col_start)
            # If there's no match_text, span to the end of the line
            if not match_text and matched_line:
                utf16_end = self._to_utf16_col(matched_line, len(matched_line))
            else:
                utf16_end = self._to_utf16_col(matched_line, col_end)

            severity_map = {"error": 1, "warning": 2, "info": 3}
            severity = severity_map.get(getattr(f, "severity", "error"), 1)

            diagnostics.append(
                {
                    "range": {
                        "start": {"line": line_no, "character": utf16_start},
                        "end": {"line": line_no, "character": utf16_end},
                    },
                    "severity": severity,
                    "code": getattr(f, "rule_id", "Unknown"),
                    "source": "zenzic",
                    "message": getattr(f, "message", "Violation found"),
                }
            )

        for s_err in snippet_errors:
            line_no = max(0, s_err.line_no - 1)
            lines = text.splitlines()
            matched_line = lines[line_no] if 0 <= line_no < len(lines) else ""
            utf16_end = self._to_utf16_col(matched_line, len(matched_line))

            diagnostics.append(
                {
                    "range": {
                        "start": {"line": line_no, "character": 0},
                        "end": {"line": line_no, "character": utf16_end},
                    },
                    "severity": 1,  # Error
                    "code": s_err.code,
                    "source": "zenzic",
                    "message": s_err.message,
                }
            )

        self.send_message(
            {
                "jsonrpc": "2.0",
                "method": "textDocument/publishDiagnostics",
                "params": {"uri": uri, "diagnostics": diagnostics},
            }
        )

    def _to_utf16_col(self, line: str, py_idx: int) -> int:
        """Convert a Python string index into a UTF-16 code unit offset."""
        col = 0
        for i, c in enumerate(line):
            if i >= py_idx:
                break
            col += 2 if ord(c) > 0xFFFF else 1
        return col
