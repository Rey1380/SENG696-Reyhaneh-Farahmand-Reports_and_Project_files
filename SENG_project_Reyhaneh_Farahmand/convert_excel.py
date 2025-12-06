import pandas as pd
import json
from pathlib import Path

EXCEL_FP = "/home/reyhaneh.farahmand/SENG696_MAS/dataset_seng.xlsx"
OUT_JSON = "/home/reyhaneh.farahmand/SENG696_MAS/dataset_seng.json"

def main():
    df = pd.read_excel(EXCEL_FP)

    # We expect at least a column named "code"
    if "code" not in df.columns:
        raise ValueError(f"'code' column not found in {EXCEL_FP}. Columns: {df.columns}")

    samples = []
    for i, row in df.iterrows():
        code = row["code"]
        if isinstance(code, float) and pd.isna(code):
            continue
        code_str = str(code)
        file_name = f"sample_{i}.c"

        samples.append({
            "file": file_name,
            "code": code_str
        })

    Path(OUT_JSON).write_text(json.dumps(samples, indent=2), encoding="utf-8")
    print(f"Saved {len(samples)} samples to {OUT_JSON}")

if __name__ == "__main__":
    main()
