# ML Evaluation Baseline Report (Week 0)

This report establishes the quantitative baseline for customer support ticket classification and sentiment analysis using the classical ML models (TF-IDF + Naive Bayes / Logistic Regression) on a held-out, stratified test set.

---

## 1. Dataset & Split Specification

- **Source Dataset:** `data/tickets_training.csv` (Total 157 samples)
- **Train Samples:** 125 (80%)
- **Test Samples:** 32 (20%)
- **Split Methodology:** Stratified split on joint `topic_sentiment` strata, `random_state=42`
- **Data Leakage Check:**
  - Overlapping text samples: **0**
  - Data leakage status: **PASSED (No Leakage)**
  - Feature extraction (`TfidfVectorizer`) and classifiers were fitted strictly on training data only.

### Class Distributions

| Topic | Train Count | Test Count | Sentiment | Train Count | Test Count |
|:---|:---:|:---:|:---|:---:|:---:|
| **billing** | 32 | 8 | **NEGATIVE** | 76 | 20 |
| **shipping** | 32 | 8 | **POSITIVE** | 49 | 12 |
| **technical** | 32 | 8 | | | |
| **other** | 29 | 8 | | | |

---

## 2. Topic Classification Baseline

- **Model:** `MultinomialNB` on `TfidfVectorizer(ngram_range=(1,2), max_features=1000)`
- **Accuracy:** **0.8750** (87.50%)
- **Macro F1:** **0.8718**
- **Macro Precision:** **0.8865**
- **Macro Recall:** **0.8750**

### Per-Class F1 Scores
- **billing**: 0.8889
- **other**: 0.8571
- **shipping**: 0.9412
- **technical**: 0.8000

### Confusion Matrix
| True \ Pred | billing | other | shipping | technical |
|:---|:---:|:---:|:---:|:---:|
| **billing** | 8 | 0 | 0 | 0 |
| **other** | 1 | 6 | 0 | 1 |
| **shipping** | 0 | 0 | 8 | 0 |
| **technical** | 1 | 0 | 1 | 6 |


---

## 3. Sentiment Classification Baseline

- **Model:** `LogisticRegression(max_iter=1000)` on `TfidfVectorizer(ngram_range=(1,2), max_features=1000)`
- **Accuracy:** **0.7500** (75.00%)
- **Macro F1:** **0.6667**
- **Macro Precision:** **0.8571**
- **Macro Recall:** **0.6667**

### Per-Class F1 Scores
- **NEGATIVE**: 0.8333
- **POSITIVE**: 0.5000

### Confusion Matrix
| True \ Pred | NEGATIVE | POSITIVE |
|:---|:---:|:---:|
| **NEGATIVE** | 20 | 0 |
| **POSITIVE** | 8 | 4 |


---

## 4. Inference Latency Benchmarks

Measured over 3200 inferences (32 test samples across 100 repetitions):

| Component | Mean Latency (ms) | Median Latency (ms) | P95 Latency (ms) | Std Dev (ms) |
|:---|:---:|:---:|:---:|:---:|
| **Topic Prediction** | 0.408 | 0.379 | 0.561 | 0.124 |
| **Sentiment Prediction** | 0.414 | 0.380 | 0.579 | 0.260 |
| **Complete Pipeline** | 0.811 | 0.753 | 1.127 | 0.244 |

---

## 5. Artifact Verification & Reproducibility

- **Persisted Artifacts:** `models/vectorizer.joblib`, `models/topic_model.joblib`, `models/sentiment_model.joblib`
- **Data Splits:** `data/train.csv`, `data/test.csv`
- **Reproducibility Command:**
  ```bash
  python -m eval.evaluate
  ```
