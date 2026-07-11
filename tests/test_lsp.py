# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for the Zenzic Language Server (ZLS) foundation."""

import io
import json

from zenzic.lsp.documents import DocumentManager
from zenzic.lsp.server import LanguageServer


def test_document_manager_incremental_sync() -> None:
    """Verify the DocumentManager correctly applies multi-line incremental edits."""
    manager = DocumentManager()
    uri = "file:///fake/path/doc.md"

    # 1. didOpen
    manager.did_open({"textDocument": {"uri": uri, "text": "Line 1\nLine 2\nLine 3\n"}})
    assert manager.documents[uri] == "Line 1\nLine 2\nLine 3\n"

    # 2. didChange (incremental: replace "Line 2" with "Modified Line 2")
    manager.did_change(
        {
            "textDocument": {"uri": uri},
            "contentChanges": [
                {
                    "range": {
                        "start": {"line": 1, "character": 0},
                        "end": {"line": 1, "character": 6},
                    },
                    "text": "Modified Line 2",
                }
            ],
        }
    )
    assert manager.documents[uri] == "Line 1\nModified Line 2\nLine 3\n"

    # 3. didChange (incremental with multi-byte unicode surrogate)
    # 📝 (U+1F4DD, memo) takes 2 UTF-16 code units.
    # text: "Line 1\n📝 Note\nLine 3\n"
    manager.documents[uri] = "Line 1\n📝 Note\nLine 3\n"
    manager.did_change(
        {
            "textDocument": {"uri": uri},
            "contentChanges": [
                {
                    "range": {
                        "start": {"line": 1, "character": 2},  # skip 📝 (2 units)
                        "end": {"line": 1, "character": 7},  # " Note" length is 5. 2 + 5 = 7.
                    },
                    "text": " Changed",
                }
            ],
        }
    )
    assert manager.documents[uri] == "Line 1\n📝 Changed\nLine 3\n"

    # 4. didChange (full sync fallback)
    manager.did_change(
        {"textDocument": {"uri": uri}, "contentChanges": [{"text": "Complete overwrite"}]}
    )
    assert manager.documents[uri] == "Complete overwrite"

    # 5. didClose
    manager.did_close({"textDocument": {"uri": uri}})
    assert uri not in manager.documents


def test_language_server_lifecycle() -> None:
    """Verify JSON-RPC 2.0 lifecycle handlers over stdio streams."""
    # Build a mock input stream
    req1 = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    req2 = {"jsonrpc": "2.0", "method": "initialized", "params": {}}
    req3 = {"jsonrpc": "2.0", "id": 2, "method": "shutdown", "params": {}}
    req4 = {"jsonrpc": "2.0", "method": "exit", "params": {}}

    def encode_rpc(msg: dict) -> bytes:
        body = json.dumps(msg, separators=(",", ":")).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        return header + body

    in_stream = io.BytesIO()
    in_stream.write(encode_rpc(req1))
    in_stream.write(encode_rpc(req2))
    in_stream.write(encode_rpc(req3))
    in_stream.write(encode_rpc(req4))
    in_stream.seek(0)

    out_stream = io.BytesIO()

    server = LanguageServer(stdin=in_stream, stdout=out_stream)
    server.serve()

    # The server loop should exit cleanly
    assert server.exit_received is True
    assert server.exit_code == 0

    out_stream.seek(0)
    output = out_stream.read()
    assert b"Content-Length" in output

    # Find the initialize response
    # It should have textDocumentSync = 2
    parts = output.split(b"\r\n\r\n")
    # first part is header, second part is body
    body_str = parts[1].split(b"Content-Length")[0]  # isolate first response body
    resp = json.loads(body_str.decode("utf-8"))

    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 1
    assert resp["result"]["capabilities"]["textDocumentSync"] == 2


def test_publish_diagnostics() -> None:
    """Verify that didChange triggers publishDiagnostics for Z-Codes."""
    # We will trigger Z107 (Circular Anchor) by writing a circular link:
    # [my heading](#my-heading)
    # Z107 rule is active by default.

    uri = "file:///fake/path/doc.md"
    req0 = {
        "jsonrpc": "2.0",
        "method": "textDocument/didOpen",
        "params": {"textDocument": {"uri": uri, "text": ""}},
    }
    req1 = {
        "jsonrpc": "2.0",
        "method": "textDocument/didChange",
        "params": {
            "textDocument": {"uri": uri},
            "contentChanges": [{"text": "Line 1\n[my heading](#my-heading)\nLine 3"}],
        },
    }
    req2 = {"jsonrpc": "2.0", "method": "exit", "params": {}}

    def encode_rpc(msg: dict) -> bytes:
        import json

        body = json.dumps(msg, separators=(",", ":")).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        return header + body

    in_stream = io.BytesIO()
    in_stream.write(encode_rpc(req0))
    in_stream.write(encode_rpc(req1))
    in_stream.write(encode_rpc(req2))
    in_stream.seek(0)

    out_stream = io.BytesIO()

    server = LanguageServer(stdin=in_stream, stdout=out_stream)
    server.serve()

    out_stream.seek(0)
    output = out_stream.read()

    # Check that a publishDiagnostics was emitted
    import json

    parts = output.split(b"\r\n\r\n")
    # find publishDiagnostics in any of the body parts
    found = False
    for p in parts:
        if b"publishDiagnostics" in p:
            body_str = p.split(b"Content-Length")[0]
            try:
                resp = json.loads(body_str.decode("utf-8"))
                if resp.get("method") == "textDocument/publishDiagnostics":
                    diagnostics = resp["params"]["diagnostics"]
                    assert len(diagnostics) > 0
                    assert diagnostics[0]["code"] == "Z107"
                    found = True
                    break
            except json.JSONDecodeError:
                pass
    assert found


def test_debounce_diagnostics() -> None:
    """Verify that multiple rapid didChange events result in a single publishDiagnostics."""
    # We send 3 didChange events for the same file, then an exit.
    # We should only see 1 publishDiagnostics.
    uri = "file:///fake/path/doc.md"
    req0 = {
        "jsonrpc": "2.0",
        "method": "textDocument/didOpen",
        "params": {"textDocument": {"uri": uri, "text": ""}},
    }
    req1 = {
        "jsonrpc": "2.0",
        "method": "textDocument/didChange",
        "params": {"textDocument": {"uri": uri}, "contentChanges": [{"text": "Line 1"}]},
    }
    req2 = {
        "jsonrpc": "2.0",
        "method": "textDocument/didChange",
        "params": {
            "textDocument": {"uri": uri},
            "contentChanges": [{"text": "Line 1\n[my heading](#my-heading)"}],
        },
    }
    req3 = {
        "jsonrpc": "2.0",
        "method": "textDocument/didChange",
        "params": {
            "textDocument": {"uri": uri},
            "contentChanges": [{"text": "Line 1\n[my heading](#my-heading)\nLine 3"}],
        },
    }
    req4 = {"jsonrpc": "2.0", "method": "exit", "params": {}}

    def encode_rpc(msg: dict) -> bytes:
        import json

        body = json.dumps(msg, separators=(",", ":")).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        return header + body

    in_stream = io.BytesIO()
    in_stream.write(encode_rpc(req0))
    in_stream.write(encode_rpc(req1))
    in_stream.write(encode_rpc(req2))
    in_stream.write(encode_rpc(req3))
    in_stream.write(encode_rpc(req4))
    in_stream.seek(0)

    out_stream = io.BytesIO()

    server = LanguageServer(stdin=in_stream, stdout=out_stream)
    server.serve()

    out_stream.seek(0)
    output = out_stream.read()

    parts = output.split(b"\r\n\r\n")
    publish_count = 0
    for p in parts:
        if b"publishDiagnostics" in p:
            body_str = p.split(b"Content-Length")[0]
            try:
                import json

                resp = json.loads(body_str.decode("utf-8"))
                if resp.get("method") == "textDocument/publishDiagnostics":
                    publish_count += 1
            except json.JSONDecodeError:
                pass

    assert publish_count == 1
