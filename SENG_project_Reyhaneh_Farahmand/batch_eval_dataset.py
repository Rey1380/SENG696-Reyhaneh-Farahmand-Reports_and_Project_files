import json
import os
import requests
import csv
from pathlib import Path

BASE_DIR = Path("/home/reyhaneh.farahmand/SENG696_MAS")
DATA_JSON = BASE_DIR / "dataset_seng.json"
OUT_JSON = BASE_DIR / "dataset_results.json"
OUT_CSV  = BASE_DIR / "dataset_results.csv"

# Endpoints – must match your running Flask services
AI_DET_URL = "http://127.0.0.1:8081/analyze"
SEV_URL    = "http://127.0.0.1:8082/severity"


def main():
    # 1) Load JSON dataset
    if not DATA_JSON.exists():
        raise FileNotFoundError(f"{DATA_JSON} not found. Run convert_excel.py first.")

    samples = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    print(f"Loaded {len(samples)} samples from {DATA_JSON}\n")

    results = []

    for idx, item in enumerate(samples, start=1):
        file_name = item["file"]
        code = item["code"]

        print(f"=== [{idx}/{len(samples)}] {file_name} ===")

        # 2) Call AI detector
        det_payload = {
            "file": file_name,  # extra info; the Flask /analyze ignores it
            "code": code
        }

        det_resp = requests.post(AI_DET_URL, json=det_payload, timeout=300)
        det_resp.raise_for_status()
        det_json = det_resp.json()

        # derive ai_label from 'label'
        label_str = det_json.get("label", "Human")
        ai_label = 1 if str(label_str).lower() == "ai" else 0

        # 3) Call severity service
        sev_payload = {
            "file": file_name,
            "code": code,
            "ai_label": ai_label
        }

        sev_resp = requests.post(SEV_URL, json=sev_payload, timeout=300)
        sev_resp.raise_for_status()
        sev_json = sev_resp.json()

        severity_text = sev_json.get("severity_text", "LOW")
        severity_score = sev_json.get("severity_score", 1)
        risk_score = sev_json.get("risk_score", severity_score)

        print(f"  AI label : {ai_label} ({label_str})")
        print(f"  Severity : {severity_text} (score={severity_score})")
        print(f"  Risk     : {risk_score}\n")

        results.append({
            "file": file_name,
            "code": code,
            "label": label_str,
            "ai_label": ai_label,
            "severity_text": severity_text,
            "severity_score": severity_score,
            "risk_score": risk_score
        })

    # 4) Save JSON
    OUT_JSON.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSaved detailed JSON results to {OUT_JSON}")

    # 5) Save CSV
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["file", "label", "ai_label", "severity_text", "severity_score", "risk_score", "code"])
        for r in results:
            writer.writerow([
                r["file"],
                r["label"],
                r["ai_label"],
                r["severity_text"],
                r["severity_score"],
                r["risk_score"],
                r["code"]
            ])
    print(f"Saved CSV results to {OUT_CSV}")


if __name__ == "__main__":
    main()

