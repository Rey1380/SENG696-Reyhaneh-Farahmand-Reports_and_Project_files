from transformers import RobertaTokenizer, RobertaForSequenceClassification
import torch

class CodeBERTDetector:
    def __init__(self, model_dir):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = RobertaTokenizer.from_pretrained(model_dir)
        self.model = RobertaForSequenceClassification.from_pretrained(model_dir)
        self.model.to(self.device)
        self.model.eval()

    @torch.inference_mode()
    def predict(self, code_str):
        inputs = self.tokenizer(
            code_str,
            truncation=True,
            padding="max_length",
            max_length=512,
            return_tensors="pt"
        ).to(self.device)

        outputs = self.model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1).cpu().numpy().flatten()

        label = int(probs[1] > probs[0])
        return {
            "label": "AI" if label else "Human",
            "confidence": float(probs[label])
        }
