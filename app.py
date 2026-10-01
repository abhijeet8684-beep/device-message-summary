import os

from flask import Flask, jsonify

from summarizer import summarize_file

app = Flask(__name__)


@app.get("/summary")
def get_summary():
    sample_file = os.environ.get("SAMPLE_FILE", "data/sample.jsonl")
    try:
        summary = summarize_file(sample_file)
    except OSError:
        return (
            jsonify(
                {
                    "error": {
                        "code": "SAMPLE_FILE_UNREADABLE",
                        "message": f"Unable to read sample file: {sample_file}",
                    }
                }
            ),
            500,
        )

    return jsonify(summary)


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5000)
