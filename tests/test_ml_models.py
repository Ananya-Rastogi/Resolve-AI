"""
Tests for ML models and predictions.
"""
import unittest
from app.models.ml_models import detect_topic, detect_sentiment, get_pipeline


class TestMLModels(unittest.TestCase):

    def test_pipeline_initialization(self):
        pipeline = get_pipeline()
        self.assertTrue(pipeline._is_trained)
        self.assertIsNotNone(pipeline.vectorizer)
        self.assertIsNotNone(pipeline.topic_model)
        self.assertIsNotNone(pipeline.sentiment_model)

    def test_detect_topic_predictions(self):
        # Billing example from dataset
        topic_billing = detect_topic("charged twice for same order")
        self.assertIn(topic_billing, ["billing", "shipping", "technical", "other"])
        self.assertEqual(topic_billing, "billing")

        # Shipping example
        topic_shipping = detect_topic("order delayed package not delivered")
        self.assertIn(topic_shipping, ["billing", "shipping", "technical", "other"])
        self.assertEqual(topic_shipping, "shipping")

    def test_detect_sentiment_predictions(self):
        sentiment_neg = detect_sentiment("refund not received, very bad experience")
        self.assertIn(sentiment_neg, ["POSITIVE", "NEGATIVE"])
        self.assertEqual(sentiment_neg, "NEGATIVE")

        sentiment_pos = detect_sentiment("billing support was helpful and great")
        self.assertIn(sentiment_pos, ["POSITIVE", "NEGATIVE"])
        self.assertEqual(sentiment_pos, "POSITIVE")


if __name__ == "__main__":
    unittest.main()
