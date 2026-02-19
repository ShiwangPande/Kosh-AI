"""Unit tests for Learning System."""
import unittest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import asyncio

from backend.services.learning.weight_optimizer import optimize_weights
from backend.services.learning.feedback_logger import log_feedback

class TestLearningSystem(unittest.IsolatedAsyncioTestCase):

    def test_weight_optimizer_logic(self):
        # 1. Accepted 'price' -> Price weight should increase
        current = {"price_weight": 0.25, "speed_weight": 0.25, "other": 0.5}
        feedback = [
            {"accepted": True, "dominant_factors": ["price"]},
            {"accepted": True, "dominant_factors": ["price"]},
        ]
        
        new_weights = optimize_weights(current, feedback, learning_rate=0.1)
        
        self.assertTrue(new_weights["price_weight"] > 0.25)
        self.assertTrue(sum(new_weights.values()) == 1.0) # approx
        
        # 2. Rejected 'speed' -> Speed weight should decrease
        current = {"price_weight": 0.25, "speed_weight": 0.25, "other": 0.5}
        feedback = [
            {"accepted": False, "dominant_factors": ["speed"]},
        ]
        new_weights = optimize_weights(current, feedback, learning_rate=0.1)
        
        self.assertTrue(new_weights["speed_weight"] < 0.25)

    async def test_feedback_logger(self):
        mock_db = AsyncMock()
        await log_feedback(
            mock_db, uuid4(), uuid4(), True, uuid4(), 5.0, 10.0
        )
        self.assertTrue(mock_db.add.called)
        self.assertTrue(mock_db.commit.called)

if __name__ == '__main__':
    unittest.main()
