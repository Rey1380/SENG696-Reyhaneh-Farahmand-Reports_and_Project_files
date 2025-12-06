import os
import logging
import numpy as np
import pandas as pd
import torch
import matplotlib.pyplot as plt
from datasets import Dataset
from transformers import RobertaTokenizer, RobertaForSequenceClassification, Trainer, TrainingArguments, set_seed
from sklearn.model_selection import GroupKFold, ParameterGrid
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

# Set seed for reproducibility
SEED = 42
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)
set_seed(SEED)

# Paths
data_dir = "/home/reyhaneh.farahmand/CodeBERT"
train_csv = os.path.join(data_dir, "aes_train.csv")
test_csv = os.path.join(data_dir, "aes_test.csv")
output_dir = os.path.join(data_dir, "codebert_repo_kfold_all_version")
model_cache = os.path.join(data_dir, "hf_cache")
os.makedirs(output_dir, exist_ok=True)

# Logging
logging.basicConfig(
    filename=os.path.join(output_dir, "log.txt"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logging.getLogger().addHandler(logging.StreamHandler())
logging.info("Starting full Grid Search with final model saving, plots and STD calculation")

# Load data
df_train = pd.read_csv(train_csv)
df_test = pd.read_csv(test_csv)
labels = df_train.label.values
groups = df_train.repo_id.values

# Tokenizer
model_name = "microsoft/codebert-base"
tokenizer = RobertaTokenizer.from_pretrained(model_name, cache_dir=model_cache)

def tokenize_data(df):
    dataset = Dataset.from_pandas(df, preserve_index=False)
    dataset = dataset.map(lambda x: tokenizer(x["code"], padding="max_length", truncation=True, max_length=512), batched=True)
    dataset = dataset.remove_columns(["code"])
    return dataset

full_dataset = tokenize_data(df_train)
test_dataset = tokenize_data(df_test)

# Metrics
def compute_metrics(eval_pred):
    logits, labels_np = eval_pred
    preds = np.argmax(logits, axis=1)
    probs = torch.nn.functional.softmax(torch.tensor(logits), dim=1).numpy()[:, 1]
    acc = accuracy_score(labels_np, preds)
    f1 = f1_score(labels_np, preds, average="macro")
    try:
        auc = roc_auc_score(labels_np, probs)
    except ValueError:
        auc = float("nan")
    return {"accuracy": acc, "f1": f1, "auc": auc}

# Hyperparameter Grid
param_grid = list(ParameterGrid({
    "learning_rate": [2e-5, 5e-5],
    "num_train_epochs": [3, 5],
    "per_device_train_batch_size": [8, 16],
}))

# Cross-validation
gkf = GroupKFold(n_splits=5)
all_results = []

for i, params in enumerate(param_grid, start=1):
    model_name_id = f"Model_{i}"
    logging.info(f"\n===== Evaluating {model_name_id} with Params: {params} =====")

    fold_metrics = []

    for fold_idx, (train_idx, val_idx) in enumerate(gkf.split(full_dataset, labels, groups), start=1):
        train_dataset = full_dataset.select(train_idx)
        val_dataset = full_dataset.select(val_idx)

        model = RobertaForSequenceClassification.from_pretrained(model_name, num_labels=2, cache_dir=model_cache)

        args = TrainingArguments(
            output_dir=os.path.join(output_dir, f"temp_{model_name_id}_fold{fold_idx}"),
            evaluation_strategy="epoch",
            learning_rate=params["learning_rate"],
            per_device_train_batch_size=params["per_device_train_batch_size"],
            per_device_eval_batch_size=params["per_device_train_batch_size"],
            num_train_epochs=params["num_train_epochs"],
            weight_decay=0.01,
            disable_tqdm=True,
            save_strategy="no",
            logging_dir=os.path.join(output_dir, f"logs_{model_name_id}_fold{fold_idx}"),
            report_to=[],
            seed=SEED,
        )

        trainer = Trainer(
            model=model,
            args=args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            compute_metrics=compute_metrics,
        )

        trainer.train()

        raw_metrics = trainer.evaluate()
        metrics = {k.replace("eval_", ""): v for k, v in raw_metrics.items()}
        metrics.update(params)
        metrics["fold"] = fold_idx
        metrics["model_version"] = model_name_id
        fold_metrics.append(metrics)

        del model
        torch.cuda.empty_cache()

    # Mean and STD
    df_fold = pd.DataFrame(fold_metrics)
    mean_metrics = df_fold.mean(numeric_only=True).to_dict()
    std_metrics = df_fold.std(numeric_only=True).to_dict()
    for k in std_metrics:
        mean_metrics[k + "_std"] = std_metrics[k]
    mean_metrics.update(params)
    mean_metrics["model_version"] = model_name_id
    all_results.append(mean_metrics)

    # Plot
    plt.figure(figsize=(8, 5))
    plt.plot(df_fold["fold"], df_fold["accuracy"], marker='o', label="Accuracy")
    plt.plot(df_fold["fold"], df_fold["auc"], marker='x', label="AUC")
    plt.xlabel("Fold")
    plt.ylabel("Score")
    plt.title(f"{model_name_id} - Accuracy & AUC per Fold")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, f"{model_name_id}_fold_performance.png"))
    plt.close()

    # Final Training
    logging.info(f"Retraining {model_name_id} on full training set...")
    final_model = RobertaForSequenceClassification.from_pretrained(model_name, num_labels=2, cache_dir=model_cache)
    final_output_dir = os.path.join(output_dir, f"final_model_{model_name_id}")
    os.makedirs(final_output_dir, exist_ok=True)

    final_args = TrainingArguments(
        output_dir=final_output_dir,
        evaluation_strategy="no",
        save_strategy="no",
        learning_rate=params["learning_rate"],
        per_device_train_batch_size=params["per_device_train_batch_size"],
        num_train_epochs=params["num_train_epochs"],
        weight_decay=0.01,
        disable_tqdm=True,
        report_to=[],
        seed=SEED,
    )

    final_trainer = Trainer(
        model=final_model,
        args=final_args,
        train_dataset=full_dataset,
    )
    final_trainer.train()
    final_trainer.save_model(final_output_dir)
    tokenizer.save_pretrained(final_output_dir)

    logging.info(f"Evaluating {model_name_id} on unseen test set...")
    test_preds = final_trainer.predict(test_dataset)
    test_metrics = compute_metrics((test_preds.predictions, test_preds.label_ids))
    pd.DataFrame([test_metrics]).to_csv(os.path.join(final_output_dir, "test_results_all_versions.csv"), index=False)
    logging.info(f"Test results for {model_name_id}: {test_metrics}")

# Save all results
results_df = pd.DataFrame(all_results)
results_df.to_csv(os.path.join(output_dir, "summary_all_versions.csv"), index=False)
logging.info("All models evaluated, plotted, and saved successfully.")
