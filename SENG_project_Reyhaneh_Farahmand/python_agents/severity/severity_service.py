import os
import json
import tempfile
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

SEMGREP_TO_LEVEL = {
    "CRITICAL": "CRITICAL",
    "ERROR": "HIGH",
    "WARNING": "MEDIUM",
    "INFO": "LOW",
}

LEVEL_TO_SCORE = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4
}

AI_WEIGHT = 0.5  # 50% increased risk if the code is AI generated


def run_semgrep(code: str):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "snippet.c")
        with open(path, "w") as f:
            f.write(code)

        cmd = [
            "semgrep",
            "--config", "p/crypto-misuse",
            "--config", "p/secrets",
            "--config", "r2c-security-audit",
            "--json",
            "--quiet",
            path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            data = json.loads(result.stdout or "{}")
            findings = data.get("results", [])
        except:
            return "LOW", 1

        if not findings:
            return "LOW", 1

        max_sev = "LOW"
        for r in findings:
            raw = r.get("extra", {}).get("severity", "INFO").upper()
            sev = SEMGREP_TO_LEVEL.get(raw, "LOW")
            if LEVEL_TO_SCORE[sev] > LEVEL_TO_SCORE[max_sev]:
                max_sev = sev

        return max_sev, LEVEL_TO_SCORE[max_sev]


@app.route("/severity", methods=["POST"])
def severity_endpoint():
    data = request.get_json(force=True)
    file = data["file"]
    code = data["code"]
    ai_label = int(data["ai_label"])  # 1 = AI, 0 = Human

    severity_text, score = run_semgrep(code)

    if ai_label == 1:
        risk_score = score * (1 + AI_WEIGHT)
    else:
        risk_score = score

    return jsonify({
        "file": file,
        "severity_text": severity_text,
        "severity_score": score,
        "ai_label": ai_label,
        "risk_score": risk_score
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082)
