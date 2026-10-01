# Walkthrough

## 1) Project structure

The project contains the required files:

```bash
app.py
summarizer.py
data/sample.jsonl
requirements.txt
README.md
WALKTHROUGH.md
.gitignore
tests/test_summary.py
```

## 2) Main processing flow

The logic lives in `summarizer.py` and reads the JSONL file as bytes. It splits on `\n`, removes a trailing `\r`, decodes each line individually as UTF-8, validates each record, and ignores duplicates after the first valid `(device_id, sequence)` pair. The result is a summary dictionary with `accepted`, `duplicates`, `errors`, and `devices`.

## 3) Running tests

```bash
python -m pytest -q
```

The project is configured with a local pytest temp directory (`.pytest_tmp`) to avoid the Windows permission problem that can occur when pytest tries to use the global temp folder. If you want to force the same setting manually:

```bash
python -m pytest -q --basetemp=./.pytest_tmp
```

This executes the focused pytest suite covering the sample case, edge cases, and HTTP behavior.

## 4) Running the Flask server

```bash
python app.py
```

The app listens on:

```bash
http://127.0.0.1:5000
```

## 5) Calling /summary

```bash
curl http://127.0.0.1:5000/summary
```

The endpoint returns the summary JSON for the configured `SAMPLE_FILE` input or the default `data/sample.jsonl` file.

## 6) Demonstrating the failure case

To demonstrate a missing or unreadable file response:

```bash
SAMPLE_FILE=missing_file.jsonl python app.py
curl http://127.0.0.1:5000/summary
```

Expected result: HTTP 500 with a JSON payload containing `error.code = "SAMPLE_FILE_UNREADABLE"`.

## 7) One design choice

I kept the business logic in `summarizer.py` and kept Flask strictly in `app.py`. This makes the validation and aggregation logic easy to test without a running web server.

## 8) Defect found and fixed

[FILL IN — Defect found and fixed]
