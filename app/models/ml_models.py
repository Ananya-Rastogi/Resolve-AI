"""
Machine learning models for topic classification and sentiment analysis.
Supports explicit training, joblib model persistence, probability confidence extraction,
and independent predictions.
"""
from pathlib import Path
from typing import Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression


def _get_project_root() -> Path:
    """Return the absolute path to the project root directory."""
    return Path(__file__).resolve().parents[2]


def _resolve_train_data_path() -> Path:
    """Resolve the location of training data (prefers train.csv over tickets_training.csv)."""
    root = _get_project_root()
    train_path = root / "data" / "train.csv"
    if train_path.exists():
        return train_path
    legacy_path = root / "data" / "tickets_training.csv"
    if legacy_path.exists():
        return legacy_path
    return train_path


def _resolve_model_dir() -> Path:
    """Resolve the directory for persisted model artifacts."""
    return _get_project_root() / "models"


class TicketMLPipeline:
    """
    Encapsulates TF-IDF vectorization, MultinomialNB topic classification,
    and LogisticRegression sentiment analysis with joblib persistence.
    """

    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = model_dir or _resolve_model_dir()
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.topic_model: Optional[MultinomialNB] = None
        self.sentiment_model: Optional[LogisticRegression] = None
        self._is_trained = False

    def train(
        self,
        train_df: Optional[pd.DataFrame] = None,
        data_path: Optional[Path] = None,
    ) -> "TicketMLPipeline":
        """
        Explicitly train the vectorizer and classifiers on training data ONLY.
        """
        if train_df is None:
            path = data_path or _resolve_train_data_path()
            if not path.exists():
                raise FileNotFoundError(f"Training dataset not found at: {path}")
            train_df = pd.read_csv(path)

        texts = train_df["text"]
        topics = train_df["topic"]
        sentiments = train_df["sentiment"]

        # Vectorization
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=1000
        )
        X = self.vectorizer.fit_transform(texts)

        # Topic Model
        self.topic_model = MultinomialNB()
        self.topic_model.fit(X, topics)

        # Sentiment Model
        self.sentiment_model = LogisticRegression(max_iter=1000)
        self.sentiment_model.fit(X, sentiments)

        self._is_trained = True
        return self

    def save(self, model_dir: Optional[Path] = None) -> None:
        """Persist trained model artifacts to disk using joblib."""
        if not self._is_trained or not self.vectorizer or not self.topic_model or not self.sentiment_model:
            raise RuntimeError("Cannot save pipeline: models have not been trained yet.")

        target_dir = model_dir or self.model_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        joblib.dump(self.vectorizer, target_dir / "vectorizer.joblib")
        joblib.dump(self.topic_model, target_dir / "topic_model.joblib")
        joblib.dump(self.sentiment_model, target_dir / "sentiment_model.joblib")

    def load(self, model_dir: Optional[Path] = None) -> "TicketMLPipeline":
        """Load persisted model artifacts from disk."""
        target_dir = model_dir or self.model_dir
        vec_path = target_dir / "vectorizer.joblib"
        topic_path = target_dir / "topic_model.joblib"
        sent_path = target_dir / "sentiment_model.joblib"

        if not (vec_path.exists() and topic_path.exists() and sent_path.exists()):
            raise FileNotFoundError(f"Model artifacts missing in: {target_dir}")

        self.vectorizer = joblib.load(vec_path)
        self.topic_model = joblib.load(topic_path)
        self.sentiment_model = joblib.load(sent_path)
        self._is_trained = True
        return self

    def predict_topic(self, text: str) -> str:
        """Generate topic prediction for an input text independently."""
        topic, _ = self.predict_topic_with_confidence(text)
        return topic

    def predict_topic_with_confidence(self, text: str) -> Tuple[str, float]:
        """Generate topic prediction along with model confidence probability."""
        if not self._is_trained or self.vectorizer is None or self.topic_model is None:
            raise RuntimeError("Pipeline not trained or loaded. Call train() or load() first.")
        X_test = self.vectorizer.transform([text])
        probs = self.topic_model.predict_proba(X_test)[0]
        best_idx = int(np.argmax(probs))
        return str(self.topic_model.classes_[best_idx]), float(probs[best_idx])

    def predict_sentiment(self, text: str) -> str:
        """Generate sentiment prediction for an input text independently."""
        sentiment, _ = self.predict_sentiment_with_confidence(text)
        return sentiment

    def predict_sentiment_with_confidence(self, text: str) -> Tuple[str, float]:
        """Generate sentiment prediction along with model confidence probability."""
        if not self._is_trained or self.vectorizer is None or self.sentiment_model is None:
            raise RuntimeError("Pipeline not trained or loaded. Call train() or load() first.")
        X_test = self.vectorizer.transform([text])
        probs = self.sentiment_model.predict_proba(X_test)[0]
        best_idx = int(np.argmax(probs))
        return str(self.sentiment_model.classes_[best_idx]), float(probs[best_idx])


# Global lazy singleton instance
_pipeline: Optional[TicketMLPipeline] = None


def get_pipeline(
    model_dir: Optional[Path] = None,
    auto_train_if_missing: bool = True,
) -> TicketMLPipeline:
    """
    Get or initialize the global TicketMLPipeline instance.
    Prefers loading persisted models from models/. Trains and saves on train.csv if missing.
    """
    global _pipeline
    if _pipeline is not None and _pipeline._is_trained:
        return _pipeline

    pipeline = TicketMLPipeline(model_dir=model_dir)
    try:
        pipeline.load()
    except (FileNotFoundError, RuntimeError):
        if auto_train_if_missing:
            pipeline.train()
            pipeline.save()
        else:
            raise
    _pipeline = pipeline
    return _pipeline


def train_and_save_pipeline(
    train_path: Optional[Path] = None,
    model_dir: Optional[Path] = None,
) -> TicketMLPipeline:
    """Explicitly train models on training data and persist to disk."""
    global _pipeline
    pipeline = TicketMLPipeline(model_dir=model_dir)
    pipeline.train(data_path=train_path)
    pipeline.save()
    _pipeline = pipeline
    return pipeline


def detect_topic(text: str) -> str:
    """Detect topic category from text using active pipeline."""
    return get_pipeline().predict_topic(text)


def detect_topic_with_confidence(text: str) -> Tuple[str, float]:
    """Detect topic category and probability confidence."""
    return get_pipeline().predict_topic_with_confidence(text)


def detect_sentiment(text: str) -> str:
    """Detect sentiment from text using active pipeline."""
    return get_pipeline().predict_sentiment(text)


def detect_sentiment_with_confidence(text: str) -> Tuple[str, float]:
    """Detect sentiment and probability confidence."""
    return get_pipeline().predict_sentiment_with_confidence(text)
