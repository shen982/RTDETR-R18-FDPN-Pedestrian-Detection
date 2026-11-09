"""Protect independent reproduction against corrupted inputs and accidental overwrites."""
import importlib.util
import io
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from types import SimpleNamespace
import zipfile
import threading
import pytest

spec = importlib.util.spec_from_file_location("reproduce", Path(__file__).resolve().parents[1] / "scripts/reproduce.py")
reproduce = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reproduce)

@pytest.mark.parametrize("name", ["../escape", "/absolute", "snapshot/../escape", "other/file", "snapshot\\escape"])
def test_rejects_archive_path_escape(name):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as bundle:
        bundle.writestr(name, b"content")
    with zipfile.ZipFile(stream) as bundle, pytest.raises(ValueError):
        reproduce.validate_members(bundle)

def test_rejects_archive_symlink():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as bundle:
        member = zipfile.ZipInfo("snapshot/link")
        member.create_system = 3
        member.external_attr = 0o120777 << 16
        bundle.writestr(member, "../../escape")
    with zipfile.ZipFile(stream) as bundle, pytest.raises(ValueError):
        reproduce.validate_members(bundle)

def test_modified_source_is_rejected_before_evaluation(tmp_path):
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    data = snapshot / "source.py"
    data.write_bytes(b"original")
    (snapshot / "REPRODUCTION_FILES.json").write_text(json.dumps({"source.py": {"bytes": 8, "sha256": reproduce.sha(data)}}))
    data.write_bytes(b"modified")
    with pytest.raises(RuntimeError, match="Frozen source/data differs"):
        reproduce.verify(SimpleNamespace(workspace=tmp_path), [])

def test_run_selection_and_unknown_names():
    assert len(reproduce.select_runs(SimpleNamespace(run=None, suite="all"))) == 22
    assert len(reproduce.select_runs(SimpleNamespace(run=None, suite="primary"))) == 9
    with pytest.raises(ValueError, match="Unknown --run"):
        reproduce.select_runs(SimpleNamespace(run=["not-an-experiment"], suite="all"))

def test_preserves_previous_results(tmp_path, monkeypatch):
    monkeypatch.setattr(reproduce, "verify", lambda *_: None)
    output = tmp_path / "previous-results"
    output.mkdir()
    args = SimpleNamespace(weights=None, action="evaluate", workspace=tmp_path, output=output)
    with pytest.raises(FileExistsError):
        reproduce.execute(args, [])

@pytest.mark.parametrize("corrupt_hash", [False, True])
def test_interrupted_http_download_resumes_and_requires_checksum(tmp_path, monkeypatch, corrupt_hash):
    payload = b"12345678" * (256 * 1024)
    ranges = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            byte_range = self.headers.get("Range")
            ranges.append(byte_range)
            offset = int(byte_range.split("=")[1].split("-")[0]) if byte_range else 0
            self.send_response(206 if offset else 200)
            if offset:
                self.send_header("Content-Range", f"bytes {offset}-{len(payload)-1}/{len(payload)}")
            self.send_header("Content-Length", str(len(payload) - offset))
            self.end_headers()
            # First response closes early, as observed with an interrupted proxy.
            end = 1024 * 1024 if len(ranges) == 1 else len(payload)
            self.wfile.write(payload[offset:end])
            self.close_connection = True

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setattr(reproduce.time, "sleep", lambda _: None)
    target = tmp_path / "asset.zip"
    asset = {"file": target.name, "bytes": len(payload),
             "sha256": "0" * 64 if corrupt_hash else hashlib.sha256(payload).hexdigest(),
             "url": f"http://127.0.0.1:{server.server_port}/asset"}
    try:
        if corrupt_hash:
            with pytest.raises(RuntimeError, match="Unable to download verified asset"):
                reproduce.download(asset, target, attempts=3)
            assert not target.exists()
        else:
            reproduce.download(asset, target, attempts=3)
            assert target.read_bytes() == payload
            assert ranges == [None, "bytes=1048576-"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
