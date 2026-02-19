"""Unit tests for Predictive Intelligence System."""
import unittest
from unittest.mock import AsyncMock, MagicMock
from datetime import date

from backend.services.predictions.confidence_engine import calculate_confidence, format_explanation
from backend.services.predictions.price_forecaster import forecast_price

class TestPredictiveIntelligence(unittest.IsolatedAsyncioTestCase):

    def test_confidence_calculation(self):
        # Low data
        self.assertLess(calculate_confidence(2, 0.1), 0.5)
        # High data, low variance
        self.assertGreater(calculate_confidence(20, 0.1), 0.8)
        # High variance penalty
        self.assertLess(calculate_confidence(20, 100.0), calculate_confidence(20, 0.1))

    def test_explanation_format(self):
        factors = {"trend": 0.5, "seasonality": -0.5}
        formatted = format_explanation(factors)
        self.assertEqual(formatted["primary_driver"], "trend") # First one
        self.assertEqual(len(formatted["factors"]), 2)
        
    async def test_price_forecaster_logic(self):
        mock_db = AsyncMock()
        mock_res = MagicMock()
        
        # Mock price history
        rows = [MagicMock(median_price=10.0 + i) for i in range(10)]
        mock_res.scalars().all.return_value = rows
        mock_db.execute.return_value = mock_res
        
        # Run
        pred = await forecast_price(mock_db, "prod_1", "Delhi")
        
        self.assertIsNotNone(pred)
        # Exponential smoothing should track upward trend
        self.assertGreater(pred.predicted_price, 10.0)
        self.assertEqual(pred.trend_direction, "UP")

if __name__ == '__main__':
    unittest.main()
