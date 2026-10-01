"""
Tests for Week 0 evaluation baseline: dataset loading, splitting reproducibility,
model training, persistence, predictions, metrics, and data leakage verification.
"""
import shutil
import tempfile
import unittest
from pathlib import Path
import pandas as pd

from app.models.ml_models import TicketMLPipeline
from eval.data_split import create_stratified_split, get_default_paths
from eval.evaluate import check_data_leakage, evaluate_baseline


class TestEvaluationBaseline(unittest.TestCase):

    def setUp(self):
        self.src, self.train_path, self.test_path = get_default_paths()
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_dataset_loading(self):
        """Verify train and test datasets exist, have correct schema, and have no missing values."""
        self.assertTrue(self.train_path.exists(), f"Train dataset missing at {self.train_path}")
        self.assertTrue(self.test_path.exists(), f"Test dataset missing at {self.test_path}")

        train_df = pd.read_csv(self.train_path)
        test_df = pd.read_csv(self.test_path)

        for col in ["text", "topic", "sentiment"]:
            self.assertIn(col, train_df.columns)
            self.assertIn(col, test_df.columns)

        self.assertEqual(train_df.isnull().sum().sum(), 0)
        self.assertEqual(test_df.isnull().sum().sum(), 0)
        self.assertEqual(len(train_df), 125)
        self.assertEqual(len(test_df), 32)

    def test_train_test_split_reproducibility(self):
        """Verify that splitting with random_state=42 is deterministic and reproducible."""
        tmp_train = self.temp_dir / "train_tmp.csv"
        tmp_test = self.temp_dir / "test_tmp.csv"

        df_train, df_test = create_stratified_split(
            input_path=self.src,
            train_path=tmp_train,
            test_path=tmp_test,
            test_size=0.2,
            random_state=42,
        )

        expected_train = pd.read_csv(self.train_path)
        expected_test = pd.read_csv(self.test_path)

        self.assertEqual(len(df_train), len(expected_train))
        self.assertEqual(len(df_test), len(expected_test))
        self.assertListEqual(df_train["text"].tolist(), expected_train["text"].tolist())
        self.assertListEqual(df_test["text"].tolist(), expected_test["text"].tolist())

    def test_no_data_leakage(self):
        """Verify test set examples are not present in training data."""
        train_df = pd.read_csv(self.train_path)
        test_df = pd.read_csv(self.test_path)

        leakage_info = check_data_leakage(train_df, test_df)
        self.assertFalse(leakage_info["has_leakage"])
        self.assertEqual(leakage_info["overlapping_samples_count"], 0)

    def test_model_training_and_saving(self):
        """Verify explicit model training on train.csv and joblib persistence."""
        pipeline = TicketMLPipeline(model_dir=self.temp_dir)
        pipeline.train(data_path=self.train_path)
        pipeline.save(self.temp_dir)

        self.assertTrue((self.temp_dir / "vectorizer.joblib").exists())
        self.assertTrue((self.temp_dir / "topic_model.joblib").exists())
        self.assertTrue((self.temp_dir / "sentiment_model.joblib").exists())

    def test_model_loading_and_prediction(self):
        """Verify loading persisted models and generating independent predictions."""
        # Train and save in temp dir
        p1 = TicketMLPipeline(model_dir=self.temp_dir)
        p1.train(data_path=self.train_path)
        p1.save(self.temp_dir)

        # Load into new instance
        p2 = TicketMLPipeline(model_dir=self.temp_dir)
        p2.load()

        topic_pred = p2.predict_topic("payment deducted twice for order")
        sentiment_pred = p2.predict_sentiment("very happy with great support")

        self.assertEqual(topic_pred, "billing")
        self.assertEqual(sentiment_pred, "POSITIVE")

    def test_evaluation_metrics_computation(self):
        """Verify evaluation metrics are calculated properly on test set."""
        results = evaluate_baseline(
            train_path=self.train_path,
            test_path=self.test_path,
            model_dir=Path(__file__).resolve().parents[1] / "models",
            repetitions=5,
        )

        top = results["topic_classification"]
        sent = results["sentiment_classification"]

        self.assertGreaterEqual(top["accuracy"], 0.0)
        self.assertLessEqual(top["accuracy"], 1.0)
        self.assertGreaterEqual(top["macro_f1"], 0.0)
        self.assertLessEqual(top["macro_f1"], 1.0)

        self.assertGreaterEqual(sent["accuracy"], 0.0)
        self.assertLessEqual(sent["accuracy"], 1.0)
        self.assertGreaterEqual(sent["macro_f1"], 0.0)
        self.assertLessEqual(sent["macro_f1"], 1.0)

        self.assertEqual(len(top["confusion_matrix"]), 4)
        self.assertEqual(len(sent["confusion_matrix"]), 2)


if __name__ == "__main__":
    unittest.main()
