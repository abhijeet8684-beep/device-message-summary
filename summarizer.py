import json

VALID_KEYS = {"device_id", "sequence", "status"}
VALID_STATUS = {"ok", "error"}


def _reject_constant(value):
    raise ValueError(f"Unsupported JSON constant: {value}")


def _is_valid_record(record):
    if not isinstance(record, dict):
        return False
    if set(record.keys()) != VALID_KEYS:
        return False

    device_id = record["device_id"]
    sequence = record["sequence"]
    status = record["status"]

    if not isinstance(device_id, str) or device_id == "" or device_id.strip() == "":
        return False
    if type(sequence) is not int or sequence < 0:
        return False
    if not isinstance(status, str) or status not in VALID_STATUS:
        return False
    return True


def summarize_bytes(raw_bytes):
    if raw_bytes == b"":
        return {"accepted": 0, "duplicates": 0, "errors": [], "devices": []}

    accepted = 0
    duplicates = 0
    errors = []
    seen = set()
    device_stats = {}
    lines = raw_bytes.split(b"\n")
    if raw_bytes.endswith(b"\n"):
        lines = lines[:-1]

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip(b"\r")

        if line.strip() == b"":
            errors.append({"line": line_number, "code": "BAD_JSON"})
            continue

        try:
            text = line.decode("utf-8")
        except UnicodeDecodeError:
            errors.append({"line": line_number, "code": "BAD_JSON"})
            continue

        try:
            parsed = json.loads(text, parse_constant=_reject_constant)
        except (TypeError, ValueError, json.JSONDecodeError):
            errors.append({"line": line_number, "code": "BAD_JSON"})
            continue

        if not _is_valid_record(parsed):
            errors.append({"line": line_number, "code": "INVALID_RECORD"})
            continue

        key = (parsed["device_id"], parsed["sequence"])
        if key in seen:
            duplicates += 1
            continue

        seen.add(key)
        accepted += 1

        device_id = parsed["device_id"]
        stats = device_stats.setdefault(
            device_id,
            {"device_id": device_id, "ok": 0, "error": 0, "last_sequence": None, "last_status": None},
        )

        status = parsed["status"]
        if status == "ok":
            stats["ok"] += 1
        else:
            stats["error"] += 1

        if stats["last_sequence"] is None or parsed["sequence"] > stats["last_sequence"]:
            stats["last_sequence"] = parsed["sequence"]
            stats["last_status"] = status

    devices = []
    for device_id in sorted(device_stats):
        stats = device_stats[device_id]
        devices.append(
            {
                "device_id": stats["device_id"],
                "ok": stats["ok"],
                "error": stats["error"],
                "last_sequence": stats["last_sequence"],
                "last_status": stats["last_status"],
            }
        )

    return {
        "accepted": accepted,
        "duplicates": duplicates,
        "errors": errors,
        "devices": devices,
    }


def summarize_file(file_path):
    with open(file_path, "rb") as source:
        return summarize_bytes(source.read())
