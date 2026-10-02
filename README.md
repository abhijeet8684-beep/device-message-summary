# Device Message Summary

A small Python and Flask application that reads synthetic device messages from a JSON Lines file and returns a
validated, deduplicated per-device summary through an HTTP endpoint.

## Walkthrough Video

TODO(author): VIDEO_OR_SCREENSHOT_URL

## Table of Contents

- [Walkthrough Video](#walkthrough-video)
1. [Overview](#1-overview)
2. [Architecture & Processing Flow](#2-architecture--processing-flow)
3. [Repository Structure](#3-repository-structure)
4. [Requirements](#4-requirements)
5. [Installation](#5-installation)
6. [Running the Application](#6-running-the-application)
7. [Input Format](#7-input-format)
8. [Processing Rules](#8-processing-rules)
9. [API Reference](#9-api-reference)
10. [Sample Input & Expected Output](#10-sample-input--expected-output)
11. [Verification Evidence](#11-verification-evidence)
12. [Testing](#12-testing)
13. [Failure Handling](#13-failure-handling)
14. [Assumptions](#14-assumptions)
15. [Known Limitation](#15-known-limitation)
16. [Out of Scope](#16-out-of-scope)
17. [Design Choice & Defect Fixed](#17-design-choice--defect-fixed)
18. [React Integration Notes](#18-react-integration-notes)

## 1. Overview

The program processes one simulated device message per JSONL line. It validates records, detects duplicate
`(device_id, sequence)` pairs, aggregates accepted `ok` and `error` messages by device, and returns the summary as
JSON from a Flask endpoint. The project is intentionally small and uses a local sample file rather than a database
or external service.

## 2. Architecture & Processing Flow

The summary logic is implemented in `summarizer.py`, independently of Flask. `app.py` reads the configured file
for each request, calls the summarizer, and returns the resulting JSON.

```mermaid
flowchart LR
    A[JSONL Input] --> B[JSON Parsing]
    B --> C[Record Validation]
    C -->|Invalid JSON or UTF-8| X[Record BAD_JSON]
    C -->|Valid JSON, invalid record| Y[Record INVALID_RECORD]
    C -->|Valid record| D[Duplicate Check]
    D -->|Previously accepted key| E[Count Duplicate]
    D -->|First valid occurrence| F[Per-device Aggregation]
    X --> G[Continue through input]
    Y --> G
    E --> G
    F --> G
    G --> H[Build Sorted Summary]
    H --> I[Flask GET /summary JSON Response]
```

## 3. Repository Structure

| Path | Purpose |
| --- | --- |
| `app.py` | Flask application and `GET /summary` endpoint. |
| `summarizer.py` | Byte-oriented JSONL parsing, validation, duplicate detection, and aggregation. |
| `data/sample.jsonl` | Five-line synthetic input used by the example. |
| `tests/test_summary.py` | Unit and HTTP endpoint tests. |
| `requirements.txt` | Direct dependencies: Flask and pytest. |
| `pytest.ini` | Pytest options, including the project-local temp directory and import path. |
| `docs/evidence/` | Captured pytest and HTTP command output. |
| `docs/screenshots/` | Screenshots of HTTP responses and pytest output. |
| `WALKTHROUGH.md` | Short presentation script for demonstrating the project. |

## 4. Requirements

- Python 3.9+
- `pip`
- Flask and pytest, installed from `requirements.txt`

No other direct application dependencies are declared.

## 5. Installation

Run from the repository root.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

## 6. Running the Application

Start the Flask development server from the repository root:

```powershell
python app.py
```

On macOS/Linux, run the same command from the activated environment:

```bash
python app.py
```

In a second terminal, request the summary. PowerShell:

```powershell
curl.exe -sS -i http://127.0.0.1:5000/summary
```

macOS/Linux:

```bash
curl -sS -i http://127.0.0.1:5000/summary
```

By default, the app reads `data/sample.jsonl` relative to `app.py`. To use another input file, set `SAMPLE_FILE`
before starting the app. An explicitly set value is used as provided.

```powershell
$env:SAMPLE_FILE="data\another-file.jsonl"
python app.py
```

The configured file is read for each endpoint request.

## 7. Input Format

Each line is expected to contain a JSON object with exactly these fields:

```json
{"device_id": "D01", "sequence": 1, "status": "ok"}
```

| Field | Accepted values |
| --- | --- |
| `device_id` | Non-empty, non-whitespace-only string. Valid IDs are preserved exactly as supplied. |
| `sequence` | Integer greater than or equal to zero; booleans are not accepted as integers. |
| `status` | Exactly `"ok"` or `"error"`. |

## 8. Processing Rules

- The file is read as bytes, split on LF, and each line is decoded as UTF-8 separately.
- Malformed JSON, invalid UTF-8, blank or whitespace-only lines, and `NaN`, `Infinity`, or `-Infinity` are
  `BAD_JSON`.
- Valid JSON that does not meet the record schema is `INVALID_RECORD`. Errors include 1-based line numbers, remain
  in input order, and do not stop processing.
- Records are validated before duplicate detection. An invalid record cannot reserve a duplicate key.
- The duplicate key is exactly `(device_id, sequence)`. The first valid occurrence is accepted; later occurrences
  count as duplicates even if their status differs.
- Duplicates do not affect accepted totals or device counts.
- Each accepted record increments its device’s `ok` or `error` count. `last_sequence` and `last_status` are based
  on the highest accepted sequence, not arrival order.
- Devices in the result are sorted by `device_id`.

## 9. API Reference

### `GET /summary`

Request:

```powershell
curl.exe -sS -i http://127.0.0.1:5000/summary
```

On successful processing, the endpoint responds with HTTP 200 and a JSON summary containing `accepted`,
`duplicates`, `errors`, and `devices`. The specific sample result is shown in Section 10. An empty input file is
also successful and returns HTTP 200 with zero counts and empty lists.

If the configured sample cannot be read, the endpoint responds with HTTP 500 and
`{"error":{"code":"SAMPLE_FILE_UNREADABLE","message":"Unable to read sample file: <path>"}}`.

Windows PowerShell 5 aliases `curl`; use `curl.exe`. On macOS/Linux, use
`curl -sS -i http://127.0.0.1:5000/summary`.

## 10. Sample Input & Expected Output

`data/sample.jsonl` contains five records in order: D01 sequence 1 `ok`, the same record again, D02 sequence 2
`error`, one malformed line, and D01 sequence 3 `error`.

The successful response has `accepted: 3`, `duplicates: 1`, and one `BAD_JSON` entry for line 4. D01 has
`ok: 1`, `error: 1`, and latest sequence 3 with status `error`; D02 has `ok: 0`, `error: 1`, and latest sequence
2 with status `error`.

Expected summary:

```json
{
  "accepted": 3,
  "duplicates": 1,
  "errors": [
    {
      "line": 4,
      "code": "BAD_JSON"
    }
  ],
  "devices": [
    {
      "device_id": "D01",
      "ok": 1,
      "error": 1,
      "last_sequence": 3,
      "last_status": "error"
    },
    {
      "device_id": "D02",
      "ok": 0,
      "error": 1,
      "last_sequence": 2,
      "last_status": "error"
    }
  ]
}
```

The captured HTTP response body is available in
[`docs/evidence/summary_success.json`](docs/evidence/summary_success.json).

## 11. Verification Evidence

The following files contain command output captured from actual test and HTTP runs:

- [`tests_after.txt`](docs/evidence/tests_after.txt) — post-change pytest run.
- [`summary_success.json`](docs/evidence/summary_success.json) — success from the default sample, with the app
  launched outside the repository directory.
- [`summary_failure.txt`](docs/evidence/summary_failure.txt) — `curl -i` response for an unreadable sample path.

The screenshots below are embedded directly so GitHub renders them in this README:

### Successful request — HTTP 200

![Successful GET /summary](docs/screenshots/02_summary_500.png)

### Unreadable input file — HTTP 500

![Unreadable sample file](docs/screenshots/01_summary_200.png)

### Automated tests

![Pytest results](docs/screenshots/03_pytest_pass.png)

## 12. Testing

Run the full test suite from the repository root:

```powershell
python -m pytest -q
```

The same command works on macOS/Linux after activating the virtual environment.

Verified result after the hardening tests: **33 passed**. The fresh command output is in
[`docs/evidence/tests_after.txt`](docs/evidence/tests_after.txt).

Coverage includes the full sample summary, empty input, out-of-order sequences, field/type validation, malformed
and deeply nested JSON, blank lines, duplicate handling, exact ID preservation, sorting, and HTTP success/failure.

## 13. Failure Handling

To reproduce the unreadable-file case described in the API reference:

```bash
SAMPLE_FILE=missing.jsonl python app.py
```

```powershell
$env:SAMPLE_FILE="missing.jsonl"; python app.py
```

The captured HTTP 500 response is in [`docs/evidence/summary_failure.txt`](docs/evidence/summary_failure.txt).

## 14. Assumptions

- `NaN`, `Infinity`, and `-Infinity` are treated as invalid JSON and reported as `BAD_JSON`.
- A single trailing newline does not create an extra record; an additional blank line is `BAD_JSON`.
- If JSON parsing fails on a line because it is nested too deeply, that line is `BAD_JSON` and later lines continue
  to be processed.
- A UTF-8 BOM at the start of line 1 is reported as `BAD_JSON`.
- Duplicate keys inside one JSON object follow Python's JSON parser behavior: the last value wins.

## 15. Known Limitation

The whole input file and the set of duplicate keys are held in memory, so the implementation is not suited to very
large files.

## 16. Out of Scope

A React page is out of scope for this assignment. The README includes integration guidance only.

## 17. Design Choice & Defect Fixed

**Design choice:** Validation and duplicate detection are distinct steps, so invalid records do not consume a
`(device_id, sequence)` key. The summary logic is kept separate from Flask so it can be tested independently.

**Defect selected for presentation:** TODO(author): choose the defect to present.

**Discovery attribution:** TODO(author): DEFECT_FOUND_BY.

## 18. React Integration Notes

- In `useEffect`, fetch `/summary` with an `AbortController` and track state shaped like
  `{status: "loading" | "success" | "error", data, error}`.
- `fetch` does not reject on HTTP 500: check `response.ok`, read `error.message` from the JSON body, and use
  `catch` for network failures.
- Treat a result as empty when `devices.length === 0 && errors.length === 0`; `accepted === 0` alone is not empty
  because a file containing only bad lines has errors.
- Render loading, error, empty, and non-empty data as four distinct branches.
- If React runs on another port, cross-origin requests need `flask-cors` or a development-server proxy; this
  repository does not add `flask-cors`.
