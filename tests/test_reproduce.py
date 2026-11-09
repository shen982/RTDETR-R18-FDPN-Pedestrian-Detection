"""Protect independent reproduction against corrupted inputs and accidental overwrites."""
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import zipfile
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
