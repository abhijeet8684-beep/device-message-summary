# Five-Minute Presentation Script

Use this as a short demonstration guide; the README is the complete technical manual.

## 1. Overview and processing flow — 30 seconds

Introduce the JSONL-to-summary workflow and point out `app.py`, `summarizer.py`, `data/sample.jsonl`, and
`tests/test_summary.py`. Explain that `/summary` returns a per-device JSON summary.

## 2. Successful HTTP request — 1 minute

From the repository root, start the server:

```powershell
python app.py
```

In another terminal:

```powershell
curl.exe -sS http://127.0.0.1:5000/summary
```

Show [`docs/evidence/summary_success.json`](docs/evidence/summary_success.json), captured from the default sample.

## 3. HTTP failure — 1 minute

Stop the server and restart with a missing sample path:

```powershell
$env:SAMPLE_FILE="missing.jsonl"; python app.py
```

Repeat the request using `curl.exe -sS -i http://127.0.0.1:5000/summary`. Show
[`docs/evidence/summary_failure.txt`](docs/evidence/summary_failure.txt), which captures the HTTP status and
`SAMPLE_FILE_UNREADABLE` response. Stop the server and run `Remove-Item Env:SAMPLE_FILE`.

## 4. Automated tests — 1 minute

Run `python -m pytest -q` from the repository root and show
[`docs/evidence/tests_after.txt`](docs/evidence/tests_after.txt), the captured test output.

## 5. Design choice and defect — 1 minute

Explain the separation of validation and duplicate detection: invalid records do not reserve a duplicate key.

TODO(author): choose the defect to present.

For author disclosures and any video link, see the corresponding sections in [README.md](README.md).
