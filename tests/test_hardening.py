import json

import pytest

from app import app
from summarizer import summarize_bytes


def test_deeply_nested_json_is_bad_json_and_later_record_is_processed():
    nested_line = b"[" * 100000 + b"]" * 100000
    valid_record = b'{"device_id": "D01", "sequence": 1, "status": "ok"}'

    result = summarize_bytes(nested_line + b"\n" + valid_record)

    assert result["errors"] == [{"line": 1, "code": "BAD_JSON"}]
    assert result["accepted"] == 1
    assert result["devices"] == [
        {
            "device_id": "D01",
            "ok": 1,
            "error": 0,
            "last_sequence": 1,
            "last_status": "ok",
        }
    ]


def test_summary_uses_default_sample_after_working_directory_changes(monkeypatch, tmp_path):
    monkeypatch.delenv("SAMPLE_FILE", raising=False)
    monkeypatch.chdir(tmp_path)

    response = app.test_client().get("/summary")

    assert response.status_code == 200
    assert response.get_json()["accepted"] == 3


def test_summary_missing_sample_file_returns_unreadable_error(monkeypatch, tmp_path):
    missing_file = tmp_path / "missing.jsonl"
    monkeypatch.setenv("SAMPLE_FILE", str(missing_file))

    response = app.test_client().get("/summary")
    body = response.get_json()

    assert response.status_code == 500
    assert body["error"]["code"] == "SAMPLE_FILE_UNREADABLE"
    assert "accepted" not in body


def test_summary_directory_sample_path_returns_unreadable_error(monkeypatch, tmp_path):
    monkeypatch.setenv("SAMPLE_FILE", str(tmp_path))

    response = app.test_client().get("/summary")
    body = response.get_json()

    assert response.status_code == 500
    assert body["error"]["code"] == "SAMPLE_FILE_UNREADABLE"
    assert "accepted" not in body


@pytest.mark.parametrize(
    "record",
    [
        '{"device_id":"D01","sequence":true,"status":"ok"}',
        '{"device_id":"D01","sequence":1.0,"status":"ok"}',
        '{"device_id":"D01","sequence":-1,"status":"ok"}',
        '{"device_id":"   ","sequence":1,"status":"ok"}',
        '{"device_id":"D01","sequence":1,"status":"ok","extra":1}',
        '{"device_id":"D01","sequence":1}',
    ],
)
def test_invalid_records_are_reported_as_invalid_record(record):
    result = summarize_bytes(record.encode("utf-8"))

    assert result["errors"] == [{"line": 1, "code": "INVALID_RECORD"}]
    assert result["accepted"] == 0
