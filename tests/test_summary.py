import json
import os

import pytest

from app import app
from summarizer import summarize_bytes, summarize_file


def test_sample_input_expected_result(tmp_path):
    sample = tmp_path / "sample.jsonl"
    sample.write_bytes(
        b'{"device_id": "D01", "sequence": 1, "status": "ok"}\n'
        b'{"device_id": "D01", "sequence": 1, "status": "ok"}\n'
        b'{"device_id": "D02", "sequence": 2, "status": "error"}\n'
        b'{this is not json)\n'
        b'{"device_id": "D01", "sequence": 3, "status": "error"}'
    )

    result = summarize_file(str(sample))

    assert result == {
        "accepted": 3,
        "duplicates": 1,
        "errors": [{"line": 4, "code": "BAD_JSON"}],
        "devices": [
            {"device_id": "D01", "ok": 1, "error": 1, "last_sequence": 3, "last_status": "error"},
            {"device_id": "D02", "ok": 0, "error": 1, "last_sequence": 2, "last_status": "error"},
        ],
    }


def test_out_of_order_sequence_counts_by_highest_sequence():
    raw = (
        b'{"device_id": "D01", "sequence": 5, "status": "ok"}\n'
        b'{"device_id": "D01", "sequence": 3, "status": "error"}'
    )

    result = summarize_bytes(raw)

    assert result["accepted"] == 2
    assert result["duplicates"] == 0
    assert result["devices"] == [
        {"device_id": "D01", "ok": 1, "error": 1, "last_sequence": 5, "last_status": "ok"}
    ]


def test_empty_input_is_valid_success():
    result = summarize_bytes(b"")

    assert result == {"accepted": 0, "duplicates": 0, "errors": [], "devices": []}


def test_bool_sequence_is_invalid_record():
    result = summarize_bytes(b'{"device_id": "D01", "sequence": true, "status": "ok"}\n')

    assert result["errors"] == [{"line": 1, "code": "INVALID_RECORD"}]
    assert result["accepted"] == 0


def test_negative_sequence_is_invalid_record():
    result = summarize_bytes(b'{"device_id": "D01", "sequence": -1, "status": "ok"}\n')

    assert result["errors"] == [{"line": 1, "code": "INVALID_RECORD"}]


def test_float_sequence_is_invalid_record():
    result = summarize_bytes(b'{"device_id": "D01", "sequence": 1.0, "status": "ok"}\n')

    assert result["errors"] == [{"line": 1, "code": "INVALID_RECORD"}]


def test_string_sequence_is_invalid_record():
    result = summarize_bytes(b'{"device_id": "D01", "sequence": "1", "status": "ok"}\n')

    assert result["errors"] == [{"line": 1, "code": "INVALID_RECORD"}]


def test_empty_device_id_is_invalid_record():
    result = summarize_bytes(b'{"device_id": "", "sequence": 1, "status": "ok"}\n')

    assert result["errors"] == [{"line": 1, "code": "INVALID_RECORD"}]


def test_whitespace_device_id_is_invalid_record():
    result = summarize_bytes(b'{"device_id": "   ", "sequence": 1, "status": "ok"}\n')

    assert result["errors"] == [{"line": 1, "code": "INVALID_RECORD"}]


def test_non_string_device_id_is_invalid_record():
    result = summarize_bytes(b'{"device_id": 123, "sequence": 1, "status": "ok"}\n')

    assert result["errors"] == [{"line": 1, "code": "INVALID_RECORD"}]


def test_extra_key_is_invalid_record():
    result = summarize_bytes(
        b'{"device_id": "D01", "sequence": 1, "status": "ok", "extra": true}\n'
    )

    assert result["errors"] == [{"line": 1, "code": "INVALID_RECORD"}]


def test_missing_key_is_invalid_record():
    result = summarize_bytes(b'{"device_id": "D01", "sequence": 1}\n')

    assert result["errors"] == [{"line": 1, "code": "INVALID_RECORD"}]


def test_scalar_json_is_invalid_record_not_bad_json():
    result = summarize_bytes(b'123\n')

    assert result["errors"] == [{"line": 1, "code": "INVALID_RECORD"}]


def test_blank_line_is_bad_json_and_processing_continues():
    raw = b'\n{"device_id": "D01", "sequence": 1, "status": "ok"}\n'

    result = summarize_bytes(raw)

    assert result["errors"] == [{"line": 1, "code": "BAD_JSON"}]
    assert result["accepted"] == 1
    assert result["devices"] == [
        {"device_id": "D01", "ok": 1, "error": 0, "last_sequence": 1, "last_status": "ok"}
    ]


def test_nan_is_bad_json():
    result = summarize_bytes(b'NaN\n')

    assert result["errors"] == [{"line": 1, "code": "BAD_JSON"}]


def test_duplicate_with_different_status_still_duplicate():
    raw = (
        b'{"device_id": "D01", "sequence": 1, "status": "ok"}\n'
        b'{"device_id": "D01", "sequence": 1, "status": "error"}\n'
    )

    result = summarize_bytes(raw)

    assert result == {
        "accepted": 1,
        "duplicates": 1,
        "errors": [],
        "devices": [
            {"device_id": "D01", "ok": 1, "error": 0, "last_sequence": 1, "last_status": "ok"}
        ],
    }


def test_invalid_record_does_not_consume_duplicate_key():
    raw = (
        b'{"device_id": "D01", "sequence": 1, "status": "invalid"}\n'
        b'{"device_id": "D01", "sequence": 1, "status": "ok"}\n'
    )

    result = summarize_bytes(raw)

    assert result["errors"] == [{"line": 1, "code": "INVALID_RECORD"}]
    assert result["accepted"] == 1
    assert result["duplicates"] == 0
    assert result["devices"] == [
        {"device_id": "D01", "ok": 1, "error": 0, "last_sequence": 1, "last_status": "ok"}
    ]


def test_ids_are_preserved_exactly():
    raw = b'{"device_id": " D01 ", "sequence": 1, "status": "ok"}\n'

    result = summarize_bytes(raw)

    assert result["devices"][0]["device_id"] == " D01 "


def test_devices_are_sorted_by_device_id():
    raw = (
        b'{"device_id": "D02", "sequence": 2, "status": "ok"}\n'
        b'{"device_id": "D01", "sequence": 1, "status": "error"}\n'
    )

    result = summarize_bytes(raw)

    assert [item["device_id"] for item in result["devices"]] == ["D01", "D02"]


def test_http_summary_returns_success_for_sample():
    client = app.test_client()

    response = client.get("/summary")

    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert data["accepted"] == 3
    assert data["duplicates"] == 1
    assert data["errors"] == [{"line": 4, "code": "BAD_JSON"}]


def test_missing_file_returns_500_with_unreadable_code():
    client = app.test_client()
    original = os.environ.get("SAMPLE_FILE")
    os.environ["SAMPLE_FILE"] = "does_not_exist.jsonl"
    try:
        response = client.get("/summary")
    finally:
        if original is None:
            os.environ.pop("SAMPLE_FILE", None)
        else:
            os.environ["SAMPLE_FILE"] = original

    assert response.status_code == 500
    assert response.is_json
    data = response.get_json()
    assert "accepted" not in data
    assert data["error"]["code"] == "SAMPLE_FILE_UNREADABLE"
