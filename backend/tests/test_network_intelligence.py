"""Unit tests for Network Intelligence System."""
import unittest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from backend.services.network_intelligence.data_anonymizer import check_privacy_threshold, anonymize_market_data
from backend.services.network_intelligence.market_price_engine import update_market_prices

class TestNetworkIntelligence(unittest.IsolatedAsyncioTestCase):

    def test_anonymizer_logic(self):
        # Privacy threshold = 5
        self.assertFalse(check_privacy_threshold(4))
        self.assertTrue(check_privacy_threshold(5))
        
        data = [{"merchant_id": "123", "price": 10}, {"merchant_id": "456", "price": 12}]
        clean = anonymize_market_data(data)
        for item in clean:
            self.assertNotIn("merchant_id", item)

    async def test_market_price_aggregation_logic(self):
        # Mock DB
        mock_db = AsyncMock()
        mock_result = MagicMock()
        
        # Mock rows: 5 distinct merchants for same product
        # Row structure matches query: (product_id, price, merchant_id, city)
        prod_id = uuid4()
        rows = [
            MagicMock(product_id=prod_id, unit_price=10.0, merchant_id=uuid4(), city="Delhi"),
            MagicMock(product_id=prod_id, unit_price=12.0, merchant_id=uuid4(), city="Delhi"),
            MagicMock(product_id=prod_id, unit_price=14.0, merchant_id=uuid4(), city="Delhi"),
            MagicMock(product_id=prod_id, unit_price=16.0, merchant_id=uuid4(), city="Delhi"),
            MagicMock(product_id=prod_id, unit_price=18.0, merchant_id=uuid4(), city="Delhi"),
        ]
        mock_result.all.return_value = rows
        mock_db.execute.return_value = mock_result
        
        # Run
        count = await update_market_prices(mock_db, lookback_hours=24)
        
        # Expect 1 record created (5 > 5)
        self.assertEqual(count, 1)
        self.assertTrue(mock_db.add_all.called)
        
        # Check values
        args = mock_db.add_all.call_args[0][0]
        record = args[0]
        self.assertEqual(record.median_price, 14.0)
        self.assertEqual(record.merchant_count, 5)

if __name__ == '__main__':
    unittest.main()
