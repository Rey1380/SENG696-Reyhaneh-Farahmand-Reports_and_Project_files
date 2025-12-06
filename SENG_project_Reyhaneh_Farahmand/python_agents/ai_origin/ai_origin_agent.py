from flask import Flask, request, jsonify
from model_loader import CodeBERTDetector

MODEL_PATH = "./model8_best"

detector = CodeBERTDetector(MODEL_PATH)
app = Flask(__name__)

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    code = data.get("code", "")

    if not code.strip():
        return jsonify({"error": "No code provided"}), 400

    result = detector.predict(code)
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
