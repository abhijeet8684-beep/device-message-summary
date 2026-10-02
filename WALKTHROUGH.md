# Five-minute presentation script

## 1. Overview and main flow — 30 seconds

Introduce the project as a Flask endpoint backed by a JSONL summarizer. Point out `app.py`, `summarizer.py`,
`data/sample.jsonl`, and `tests/test_summary.py`. The summarizer parses and validates each line, then filters
duplicate keys before aggregating device totals.

## 2. Successful request — 1 minute

From the repository root, **Terminal 1**:

```powershell
python app.py
```

In **Terminal 2**:

```powershell
curl.exe -sS -i http://127.0.0.1:5000/summary
```

Show the HTTP 200 result in [`docs/evidence/summary_success.txt`](docs/evidence/summary_success.txt) and the
[HTTP 200 screenshot](docs/screenshots/01_summary_200.png). The sample summary accepts three records, counts one
duplicate, and reports malformed line 4 as `BAD_JSON`.

## 3. Unreadable-file failure — 1 minute

Stop Terminal 1 with `Ctrl+C`, then restart with an intentionally missing sample path:

```powershell
$env:SAMPLE_FILE="data\does-not-exist.jsonl"
python app.py
```

In Terminal 2, issue the same request:

```powershell
curl.exe -sS -i http://127.0.0.1:5000/summary
```

Show HTTP 500, `SAMPLE_FILE_UNREADABLE`, and the [failure screenshot](docs/screenshots/02_summary_500.png).
This error response is distinct from an empty successful summary. Stop the server and restore the environment:

```powershell
Remove-Item Env:SAMPLE_FILE
```

macOS/Linux equivalents: `SAMPLE_FILE=data/does-not-exist.jsonl python3 app.py`, then `unset SAMPLE_FILE`.

## 4. Tests — 1 minute

From the repository root, run:

```powershell
python -m pytest -q
```

The verified suite has 23 passing tests. Show the [pytest screenshot](docs/screenshots/03_pytest_pass.png) and
the full captured reports: [`pytest_verbose.txt`](docs/evidence/pytest_verbose.txt) and
[`pytest_plain.txt`](docs/evidence/pytest_plain.txt).

## 5. Design choice and defect fixed — 1 minute

**Design choice:** Validation occurs before duplicate detection, ensuring invalid input does not consume a key.
The processing logic is separate from Flask and can be tested directly.

**Defect found and fixed:** Deeply nested JSON could raise an uncaught `RecursionError` and abort the summary; it is
now handled per line as `BAD_JSON`. The default sample path also depended on the working directory; it is now
anchored to `app.py`. Regression tests cover both fixes.

## Additional captured evidence

- [`summary_other_cwd.txt`](docs/evidence/summary_other_cwd.txt) records HTTP 200 when the app is launched from
  outside the repository directory.
- [`summary_missing_file.txt`](docs/evidence/summary_missing_file.txt) contains the captured failure response.
