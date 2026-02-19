"""Unit tests for Autonomous Optimization Engine."""
import unittest
from unittest.mock import AsyncMock, MagicMock

from backend.services.autonomy.weight_tuner import WeightTuner
from backend.services.autonomy.performance_monitor import PerformanceMonitor

class TestAutonomyEngine(unittest.IsolatedAsyncioTestCase):

    def test_weight_tuner_logic(self):
        # Scenario: Low acceptance rate -> Increase price_weight
        current = {
            "price_weight": 0.4,
            "reliability_weight": 0.4,
            "speed_weight": 0.2
        }
        target = "acceptance_rate"
        
        new_weights = WeightTuner.adjust_weights(current, target)
        
        # Check boost
        self.assertAlmostEqual(new_weights["price_weight"], 0.45)
        
        # Check reductions
        # Remaining 0.6 -> Reduced by 0.05 total -> 0.025 each
        self.assertAlmostEqual(new_weights["reliability_weight"], 0.375)
        self.assertAlmostEqual(new_weights["speed_weight"], 0.175)
        
        # Check Sum
        total = sum(new_weights.values())
        self.assertAlmostEqual(total, 1.0)

    async def test_performance_monitor_drop_check(self):
        mock_db = AsyncMock()
        
        # Mock baseline result
        # returns scalar (avg value)
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0.50 # 50% baseline
        mock_db.execute.return_value = mock_result
        
        # Case 1: Small drop (48% -> -4%) - NO ALARM
        is_drop, base, dev = await PerformanceMonitor.check_performance_drop(mock_db, "acceptance_rate", 0.48)
        self.assertFalse(is_drop)
        
        # Case 2: Big drop (40% -> -20%) - ALARM
        is_drop, base, dev = await PerformanceMonitor.check_performance_drop(mock_db, "acceptance_rate", 0.40)
        self.assertTrue(is_drop)

if __name__ == '__main__':
    unittest.main()
