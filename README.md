# Device Message Summary

## Project overview

This project reads a JSON Lines file of simulated device messages, validates each record, removes duplicates, and produces a summary of accepted records and per-device status. The service exposes a small Flask endpoint that returns the summary as JSON.

## Prerequisites

- Python 3.9+
- Flask
- pytest
- A local virtual environment named `.venv` in the project root

## Setup

Create or reuse the project's virtual environment and ensure it is active before installing dependencies.

## Installation

```bash
python -m pip install -r requirements.txt
```

## Running the application

```bash
python app.py
```

Then open:

```bash
http://127.0.0.1:5000/summary
```

## Running tests

This repository uses a project-local pytest temp directory to avoid Windows permission issues with the default temp folder.

```bash
python -m pytest -q
```

If you need to override the temp directory explicitly on Windows, use:

```bash
python -m pytest -q --basetemp=./.pytest_tmp
```

## Example API usage

```bash
curl http://127.0.0.1:5000/summary
```

## Expected behavior

- Each valid JSON line must contain exactly `device_id`, `sequence`, and `status`.
- Invalid JSON lines are recorded as `BAD_JSON` and processing continues.
- Invalid records are recorded as `INVALID_RECORD`.
- Duplicate `(device_id, sequence)` pairs are ignored after the first valid occurrence.
- Per-device summaries are sorted by `device_id` and use the highest accepted sequence for `last_sequence` and `last_status`.

## Assumptions

1. Ambiguity: non-standard JSON constants such as `NaN`, `Infinity`, and `-Infinity` are not valid JSON.
   Assumption: they are treated as `BAD_JSON` and do not affect later records.
2. Ambiguity: whether a final newline creates an extra blank record.
   Assumption: the application treats any whitespace-only line as a `BAD_JSON` record, so the input file should not contain empty trailing lines.

## Known limitation

The application reads and processes the configured sample file on each request, which is simple and suitable for this synthetic assignment but not intended for large production data streams.

### Time spent

[FILL IN — Time spent]

### Unfinished work

[FILL IN — Unfinished work]

### AI / Reuse Note

[FILL IN — AI/reuse note]

### Defect Found and Fixed

[FILL IN — Defect found and fixed]

## React integration explanation

- A React page can call `GET /summary` from the Flask app.
- The page should treat `loading` as the state before the fetch completes.
- A successful empty result can be shown as an empty list of devices with `accepted = 0`.
- A successful non-empty result can render the `devices` array and `accepted` counts.
- API failure should show an error message when the response status is not 200 or the JSON contains an `error` object.
