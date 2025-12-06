

# AI-Assisted Security Triage for Cryptographic Code

### Multi-Agent System (MAS) + CodeBERT Classifier + Semgrep Analysis

### Comprehensive Documentation and Execution Guide

---

## 1. Overview

This project provides an automated pipeline for determining whether a C/C++ cryptographic code snippet is AI-generated or human-written, followed by a security triage process using static analysis. The system integrates:

* A fine-tuned **CodeBERT classifier** to detect AI-origin.
* **Semgrep** static analysis for identifying cryptographic misuse and security issues.
* A **multi-agent system (JADE)** handling classification, severity evaluation, risk computation, and reporting.
* A **batch evaluation pipeline** for running the full analysis on real datasets.

The system supports two execution modes:

1. **Python-only mode** for dataset evaluation.
2. **Full JADE multi-agent mode** for architectural demonstration.

---

## 2. Project Objectives

* Detect AI-generated cryptographic code using a fine-tuned language model.
* Automatically analyze code security properties using Semgrep.
* Produce risk scores by combining security severity with AI-origin results.
* Demonstrate an extensible MAS architecture for security triage research and teaching.

---

## 3. Repository Structure

```
SENG696_MAS/
│
├── python_agents/
│   ├── ai_origin/
│   │   ├── ai_origin_agent.py
│   │   ├── model_loader.py
│   │   └── model8_best/
│   │
│   ├── severity/
│       └── severity_service.py
│
├── src/masproject/
│   ├── AiOriginAgent.java
│   ├── SeverityAgent.java
│   ├── ReportAgent.java
│   ├── OrchestratorAgent.java
│   ├── TestAgent.java
│   └── JsonUtils.java
│
├── dataset_seng.xlsx
├── convert_excel.py
├── dataset_seng.json
├── batch_eval_dataset.py
│
├── output/
│   └── risk_report.json
│
└── README.md
```

---

## 4. Environment Requirements

### Required Software

* Python 3.10+
* Conda/Miniforge (recommended)
* Java OpenJDK 11
* Semgrep
* PyTorch + Transformers
* JADE
* SLURM (for ARC HPC)

GPU is optional; CPU-only inference is supported.

### Required Python Packages

```bash
pip install torch transformers flask pandas requests openpyxl
```

### Semgrep Installation

```bash
pip install semgrep
```

---

## 5. CodeBERT AI-Origin Detector

A Flask service exposes the AI-origin classifier.

### Endpoint

```
POST http://127.0.0.1:8081/analyze
```

### Request Body

```json
{ "code": "<source code>" }
```

### Response

```json
{
  "label": "AI" or "Human",
  "confidence": 0.0-1.0
}
```

The detector loads a fine-tuned CodeBERT model from:

```
python_agents/ai_origin/model8_best/
```

---

## 6. Semgrep Severity and Risk Service

Performs:

1. Semgrep scan using:

   * p/crypto-misuse
   * p/secrets
   * r2c-security-audit
2. Extracts the highest severity level.
3. Computes final risk score:

```
risk_score = severity_score * (1 + AI_WEIGHT)
```

Current:

```
AI_WEIGHT = 0.5
```

### Endpoint

```
POST http://127.0.0.1:8082/severity
```

### Input Format

```json
{
  "file": "...",
  "code": "...",
  "ai_label": 0 or 1
}
```

### Output

```json
{
  "file": "...",
  "severity_text": "...",
  "severity_score": <int>,
  "ai_label": 0 or 1,
  "risk_score": <float>
}
```

---

## 7. Multi-Agent System (JADE)

### Agents

#### 7.1 AiOriginAgent

Receives code from OrchestratorAgent → calls AI detector → returns `{file, code, ai_label}`.

#### 7.2 SeverityAgent

Receives AI-origin result → queries severity service → returns final triage output.

#### 7.3 ReportAgent

Writes final output to:

```
output/risk_report.json
```

#### 7.4 OrchestratorAgent

Coordinates the entire flow (demo mode only; does not read dataset).

---

## 8. Dataset Workflow

### 8.1 Convert Excel Dataset to JSON

```bash
python convert_excel.py
```

Produces:

```
dataset_seng.json
```

Format:

```json
[
  { "file": "sample_0.c", "code": "..." },
  ...
]
```

### 8.2 Full Dataset Evaluation

```bash
python batch_eval_dataset.py
```

Produces:

* `dataset_results.json`
* `dataset_results.csv`

JADE is **not** used for dataset evaluation.

---

## 9. Running the Entire System

### Step 1 — Start AI Detector Service (Terminal 1)

```bash
cd ~/SENG696_MAS/python_agents/ai_origin
python ai_origin_agent.py
```

Runs on port **8081**.

---

### Step 2 — Start Severity Service (Terminal 2)

```bash
cd ~/SENG696_MAS/python_agents/ai_origin
python severity_service.py
```

Runs on port **8082**.

---

### Step 3 — Start JADE Main Container (Terminal 3)

```bash
module load java/openjdk-11.0.2

java -cp jade-copy/classes:lib/*:lib/json-20210307.jar \
     jade.Boot -host 127.0.0.1 -port 1200
```

Wait for:

```
Main-Container@127.0.0.1 is ready.
```

---

### Step 4 — Compile and Start Agents (Terminal 4)

```bash
cd ~/SENG696_MAS
rm -rf classes/*
javac -cp jade-copy/classes:lib/*:lib/json-20210307.jar -d classes src/masproject/*.java

java -cp jade-copy/classes:classes:lib/*:lib/json-20210307.jar \
     jade.Boot \
     -container -host 127.0.0.1 -port 1200 \
     -agents "ai-origin:masproject.AiOriginAgent;severity:masproject.SeverityAgent;report:masproject.ReportAgent;orchestrator:masproject.OrchestratorAgent"
```

You should see:

```
AiOriginAgent started
SeverityAgent started
ReportAgent started
OrchestratorAgent started
Orchestrator → AiOriginAgent
```

---

## 10. Running Dataset Evaluation

Ensure Terminal 1 and Terminal 2 are running.

Then:

```bash
python batch_eval_dataset.py
```

Outputs:

```
dataset_results.json
dataset_results.csv
```

---

## 11. ARC Cluster Notes

* GPU is optional; CPU-only execution is sufficient for inference.
* JADE runs in headless mode (no GUI available).
* Semgrep executes normally in CPU environment.

For heavy experiments, bigmem or CPU partitions are recommended.

---

## 12. Known Limitations and Future Extensions

* OrchestratorAgent uses a hard-coded example input; dataset integration can be added.
* Semgrep rulesets may be extended with domain-specific crypto policies.
* A richer risk-scoring model can be introduced (model-based weighting, additional signals).
* MAS can be extended to distributed triage or cross-agent negotiation strategies.

---

## 13. Summary

This project integrates ML-based AI-origin detection, static analysis, and multi-agent systems to create a modular cybersecurity triage pipeline for cryptographic code. It is suitable for research, academic demonstration, and extension in secure AI-driven code analysis.




