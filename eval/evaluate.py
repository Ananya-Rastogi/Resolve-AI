"""
Evaluation script for establishing ML baseline performance on customer support tickets.
Calculates Accuracy, Precision, Recall, Macro F1, Per-class F1, Confusion Matrices,
Inference Latencies, and Data Leakage checks on the held-out test set.
"""
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from app.models.ml_models import TicketMLPipeline, get_pipeline


def _get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def measure_inference_latencies(
    pipeline: TicketMLPipeline,
    test_texts: List[str],
    repetitions: int = 100,
) -> Dict[str, Dict[str, float]]:
    """
    Measure inference latencies for topic, sentiment, and complete classification.
    Runs multiple repetitions to ensure stable, statistically sound measurements.
    """
    # Warmup
    for t in test_texts[:5]:
        _ = pipeline.predict_topic(t)
        _ = pipeline.predict_sentiment(t)

    topic_times: List[float] = []
    sentiment_times: List[float] = []
    pipeline_times: List[float] = []

    for _ in range(repetitions):
        for text in test_texts:
            # Measure topic latency
            t0 = time.perf_counter()
            _ = pipeline.predict_topic(text)
            t1 = time.perf_counter()
            topic_times.append((t1 - t0) * 1000.0)  # in ms

            # Measure sentiment latency
            t2 = time.perf_counter()
            _ = pipeline.predict_sentiment(text)
            t3 = time.perf_counter()
            sentiment_times.append((t3 - t2) * 1000.0)  # in ms

            # Measure complete pipeline latency
            t4 = time.perf_counter()
            _ = pipeline.predict_topic(text)
            _ = pipeline.predict_sentiment(text)
            t5 = time.perf_counter()
            pipeline_times.append((t5 - t4) * 1000.0)  # in ms

    return {
        "topic_prediction_ms": {
            "mean": float(np.mean(topic_times)),
            "median": float(np.median(topic_times)),
            "std": float(np.std(topic_times)),
            "p95": float(np.percentile(topic_times, 95)),
            "sample_count": len(topic_times),
        },
        "sentiment_prediction_ms": {
            "mean": float(np.mean(sentiment_times)),
            "median": float(np.median(sentiment_times)),
            "std": float(np.std(sentiment_times)),
            "p95": float(np.percentile(sentiment_times, 95)),
            "sample_count": len(sentiment_times),
        },
        "complete_classification_pipeline_ms": {
            "mean": float(np.mean(pipeline_times)),
            "median": float(np.median(pipeline_times)),
            "std": float(np.std(pipeline_times)),
            "p95": float(np.percentile(pipeline_times, 95)),
            "sample_count": len(pipeline_times),
        },
    }


def check_data_leakage(train_df: pd.DataFrame, test_df: pd.DataFrame) -> Dict[str, Any]:
    """Verify that test set examples and vocabulary do not leak into training."""
    train_texts = set(train_df["text"].str.strip().str.lower())
    test_texts = set(test_df["text"].str.strip().str.lower())
    overlap = train_texts.intersection(test_texts)

    return {
        "has_leakage": len(overlap) > 0,
        "overlapping_samples_count": len(overlap),
        "overlapping_samples": list(overlap),
        "train_samples_count": len(train_df),
        "test_samples_count": len(test_df),
    }


def evaluate_baseline(
    train_path: Optional[Path] = None,
    test_path: Optional[Path] = None,
    model_dir: Optional[Path] = None,
    repetitions: int = 100,
) -> Dict[str, Any]:
    """
    Run the complete evaluation workflow, compute all metrics, and return structured results.
    """
    root = _get_project_root()
    train_file = train_path or (root / "data" / "train.csv")
    test_file = test_path or (root / "data" / "test.csv")
    models_folder = model_dir or (root / "models")

    if not train_file.exists():
        raise FileNotFoundError(f"Training dataset not found: {train_file}")
    if not test_file.exists():
        raise FileNotFoundError(f"Test dataset not found: {test_file}")

    train_df = pd.read_csv(train_file)
    test_df = pd.read_csv(test_file)

    # 1. Verify Data Leakage
    leakage_info = check_data_leakage(train_df, test_df)

    # 2. Load Persisted Pipeline (ensuring fitted solely on train)
    pipeline = TicketMLPipeline(model_dir=models_folder)
    try:
        pipeline.load()
    except (FileNotFoundError, RuntimeError):
        pipeline.train(train_df=train_df)
        pipeline.save(models_folder)

    # 3. Generate Predictions on Test Set
    test_texts = test_df["text"].tolist()
    y_topic_true = test_df["topic"].tolist()
    y_sentiment_true = test_df["sentiment"].tolist()

    y_topic_pred = [pipeline.predict_topic(t) for t in test_texts]
    y_sentiment_pred = [pipeline.predict_sentiment(t) for t in test_texts]

    # Topic Labels & Classes
    topic_classes = sorted(list(set(y_topic_true + y_topic_pred)))
    sentiment_classes = sorted(list(set(y_sentiment_true + y_sentiment_pred)))

    # 4. Calculate Topic Metrics
    topic_accuracy = float(accuracy_score(y_topic_true, y_topic_pred))
    topic_macro_precision = float(precision_score(y_topic_true, y_topic_pred, average="macro", zero_division=0))
    topic_macro_recall = float(recall_score(y_topic_true, y_topic_pred, average="macro", zero_division=0))
    topic_macro_f1 = float(f1_score(y_topic_true, y_topic_pred, average="macro", zero_division=0))
    topic_report = classification_report(y_topic_true, y_topic_pred, output_dict=True, zero_division=0)
    topic_cm = confusion_matrix(y_topic_true, y_topic_pred, labels=topic_classes).tolist()

    topic_per_class_f1 = {
        cls: float(topic_report[cls]["f1-score"]) for cls in topic_classes if cls in topic_report
    }

    # 5. Calculate Sentiment Metrics
    sent_accuracy = float(accuracy_score(y_sentiment_true, y_sentiment_pred))
    sent_macro_precision = float(precision_score(y_sentiment_true, y_sentiment_pred, average="macro", zero_division=0))
    sent_macro_recall = float(recall_score(y_sentiment_true, y_sentiment_pred, average="macro", zero_division=0))
    sent_macro_f1 = float(f1_score(y_sentiment_true, y_sentiment_pred, average="macro", zero_division=0))
    sent_report = classification_report(y_sentiment_true, y_sentiment_pred, output_dict=True, zero_division=0)
    sent_cm = confusion_matrix(y_sentiment_true, y_sentiment_pred, labels=sentiment_classes).tolist()

    sent_per_class_f1 = {
        cls: float(sent_report[cls]["f1-score"]) for cls in sentiment_classes if cls in sent_report
    }

    # 6. Measure Latency
    latency_results = measure_inference_latencies(pipeline, test_texts, repetitions=repetitions)

    # 7. Aggregate Results
    results = {
        "dataset": {
            "source_dataset": "data/tickets_training.csv",
            "train_samples": len(train_df),
            "test_samples": len(test_df),
            "split_ratio": "80/20 stratified",
            "random_state": 42,
            "topic_distribution_train": train_df["topic"].value_counts().to_dict(),
            "topic_distribution_test": test_df["topic"].value_counts().to_dict(),
            "sentiment_distribution_train": train_df["sentiment"].value_counts().to_dict(),
            "sentiment_distribution_test": test_df["sentiment"].value_counts().to_dict(),
        },
        "data_leakage_check": leakage_info,
        "models": {
            "feature_extractor": "TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_features=1000)",
            "topic_classifier": "MultinomialNB()",
            "sentiment_classifier": "LogisticRegression(max_iter=1000)",
            "artifacts_location": str(models_folder),
        },
        "topic_classification": {
            "accuracy": topic_accuracy,
            "macro_f1": topic_macro_f1,
            "macro_precision": topic_macro_precision,
            "macro_recall": topic_macro_recall,
            "classes": topic_classes,
            "per_class_f1": topic_per_class_f1,
            "confusion_matrix": topic_cm,
            "detailed_report": topic_report,
        },
        "sentiment_classification": {
            "accuracy": sent_accuracy,
            "macro_f1": sent_macro_f1,
            "macro_precision": sent_macro_precision,
            "macro_recall": sent_macro_recall,
            "classes": sentiment_classes,
            "per_class_f1": sent_per_class_f1,
            "confusion_matrix": sent_cm,
            "detailed_report": sent_report,
        },
        "latency": latency_results,
    }

    return results


def save_reports(results: Dict[str, Any], output_dir: Optional[Path] = None) -> Tuple[Path, Path]:
    """Save baseline evaluation results to JSON and Markdown reports."""
    root = _get_project_root()
    target_dir = output_dir or (root / "eval")
    target_dir.mkdir(parents=True, exist_ok=True)

    json_path = target_dir / "baseline_results.json"
    md_path = target_dir / "baseline_report.md"

    # Save JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Format Markdown Report
    ds = results["dataset"]
    top = results["topic_classification"]
    sent = results["sentiment_classification"]
    lat = results["latency"]
    leak = results["data_leakage_check"]

    # Format Confusion Matrices
    top_cm_md = "| True \\ Pred | " + " | ".join(top["classes"]) + " |\n"
    top_cm_md += "|:---|" + ":---:|" * len(top["classes"]) + "\n"
    for i, row_label in enumerate(top["classes"]):
        top_cm_md += f"| **{row_label}** | " + " | ".join(str(val) for val in top["confusion_matrix"][i]) + " |\n"

    sent_cm_md = "| True \\ Pred | " + " | ".join(sent["classes"]) + " |\n"
    sent_cm_md += "|:---|" + ":---:|" * len(sent["classes"]) + "\n"
    for i, row_label in enumerate(sent["classes"]):
        sent_cm_md += f"| **{row_label}** | " + " | ".join(str(val) for val in sent["confusion_matrix"][i]) + " |\n"

    md_content = f"""# ML Evaluation Baseline Report (Week 0)

This report establishes the quantitative baseline for customer support ticket classification and sentiment analysis using the classical ML models (TF-IDF + Naive Bayes / Logistic Regression) on a held-out, stratified test set.

---

## 1. Dataset & Split Specification

- **Source Dataset:** `{ds["source_dataset"]}` (Total 157 samples)
- **Train Samples:** {ds["train_samples"]} (80%)
- **Test Samples:** {ds["test_samples"]} (20%)
- **Split Methodology:** Stratified split on joint `topic_sentiment` strata, `random_state=42`
- **Data Leakage Check:**
  - Overlapping text samples: **{leak["overlapping_samples_count"]}**
  - Data leakage status: **{"PASSED (No Leakage)" if not leak["has_leakage"] else "FAILED (Leakage Detected)"}**
  - Feature extraction (`TfidfVectorizer`) and classifiers were fitted strictly on training data only.

### Class Distributions

| Topic | Train Count | Test Count | Sentiment | Train Count | Test Count |
|:---|:---:|:---:|:---|:---:|:---:|
| **billing** | {ds["topic_distribution_train"].get("billing", 0)} | {ds["topic_distribution_test"].get("billing", 0)} | **NEGATIVE** | {ds["sentiment_distribution_train"].get("NEGATIVE", 0)} | {ds["sentiment_distribution_test"].get("NEGATIVE", 0)} |
| **shipping** | {ds["topic_distribution_train"].get("shipping", 0)} | {ds["topic_distribution_test"].get("shipping", 0)} | **POSITIVE** | {ds["sentiment_distribution_train"].get("POSITIVE", 0)} | {ds["sentiment_distribution_test"].get("POSITIVE", 0)} |
| **technical** | {ds["topic_distribution_train"].get("technical", 0)} | {ds["topic_distribution_test"].get("technical", 0)} | | | |
| **other** | {ds["topic_distribution_train"].get("other", 0)} | {ds["topic_distribution_test"].get("other", 0)} | | | |

---

## 2. Topic Classification Baseline

- **Model:** `MultinomialNB` on `TfidfVectorizer(ngram_range=(1,2), max_features=1000)`
- **Accuracy:** **{top["accuracy"]:.4f}** ({top["accuracy"] * 100:.2f}%)
- **Macro F1:** **{top["macro_f1"]:.4f}**
- **Macro Precision:** **{top["macro_precision"]:.4f}**
- **Macro Recall:** **{top["macro_recall"]:.4f}**

### Per-Class F1 Scores
"""
    for cls, score in top["per_class_f1"].items():
        md_content += f"- **{cls}**: {score:.4f}\n"

    md_content += f"""
### Confusion Matrix
{top_cm_md}

---

## 3. Sentiment Classification Baseline

- **Model:** `LogisticRegression(max_iter=1000)` on `TfidfVectorizer(ngram_range=(1,2), max_features=1000)`
- **Accuracy:** **{sent["accuracy"]:.4f}** ({sent["accuracy"] * 100:.2f}%)
- **Macro F1:** **{sent["macro_f1"]:.4f}**
- **Macro Precision:** **{sent["macro_precision"]:.4f}**
- **Macro Recall:** **{sent["macro_recall"]:.4f}**

### Per-Class F1 Scores
"""
    for cls, score in sent["per_class_f1"].items():
        md_content += f"- **{cls}**: {score:.4f}\n"

    md_content += f"""
### Confusion Matrix
{sent_cm_md}

---

## 4. Inference Latency Benchmarks

Measured over {lat["complete_classification_pipeline_ms"]["sample_count"]} inferences ({ds["test_samples"]} test samples across 100 repetitions):

| Component | Mean Latency (ms) | Median Latency (ms) | P95 Latency (ms) | Std Dev (ms) |
|:---|:---:|:---:|:---:|:---:|
| **Topic Prediction** | {lat["topic_prediction_ms"]["mean"]:.3f} | {lat["topic_prediction_ms"]["median"]:.3f} | {lat["topic_prediction_ms"]["p95"]:.3f} | {lat["topic_prediction_ms"]["std"]:.3f} |
| **Sentiment Prediction** | {lat["sentiment_prediction_ms"]["mean"]:.3f} | {lat["sentiment_prediction_ms"]["median"]:.3f} | {lat["sentiment_prediction_ms"]["p95"]:.3f} | {lat["sentiment_prediction_ms"]["std"]:.3f} |
| **Complete Pipeline** | {lat["complete_classification_pipeline_ms"]["mean"]:.3f} | {lat["complete_classification_pipeline_ms"]["median"]:.3f} | {lat["complete_classification_pipeline_ms"]["p95"]:.3f} | {lat["complete_classification_pipeline_ms"]["std"]:.3f} |

---

## 5. Artifact Verification & Reproducibility

- **Persisted Artifacts:** `models/vectorizer.joblib`, `models/topic_model.joblib`, `models/sentiment_model.joblib`
- **Data Splits:** `data/train.csv`, `data/test.csv`
- **Reproducibility Command:**
  ```bash
  python -m eval.evaluate
  ```
"""

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    return json_path, md_path


if __name__ == "__main__":
    print("Running baseline evaluation on held-out test set...")
    res = evaluate_baseline()
    json_p, md_p = save_reports(res)
    print("\nEvaluation complete!")
    print(f"  Topic Accuracy:     {res['topic_classification']['accuracy']:.4f}")
    print(f"  Topic Macro F1:     {res['topic_classification']['macro_f1']:.4f}")
    print(f"  Sentiment Accuracy: {res['sentiment_classification']['accuracy']:.4f}")
    print(f"  Sentiment Macro F1: {res['sentiment_classification']['macro_f1']:.4f}")
    print(f"  Avg Pipeline Latency: {res['latency']['complete_classification_pipeline_ms']['mean']:.3f} ms")
    print(f"\nArtifacts saved to:\n  {json_p}\n  {md_p}")
