"""Unit tests for Intelligence Engine modules."""
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import asyncio

from backend.services.sku_normalizer import normalize_text, compute_similarity
from backend.services.value_score_engine import calculate_subscores
from backend.services.supplier_score_engine import calculate_supplier_score
from backend.services.anomaly_detector import detect_anomalies
from backend.models.models import Supplier, InvoiceItem

class TestIntelligenceEngine(unittest.TestCase):

    # ── SKU Normalizer Tests ──────────────────────────────

    def test_normalize_text(self):
        self.assertEqual(normalize_text("The  Red   Apple! "), "red apple")
        self.assertEqual(normalize_text("Samsung Galaxy S24 (256GB)"), "samsung galaxy s24 256gb")
        self.assertEqual(normalize_text("Box of 10 Pencils"), "10 pencils")

    def test_compute_similarity(self):
        self.assertEqual(compute_similarity("apple", "apple"), 1.0)
        self.assertTrue(compute_similarity("apple", "orange") < 0.5)
        self.assertTrue(compute_similarity("iphone 15", "iphone 15 pro") > 0.8)

    # ── Value Score Tests ─────────────────────────────────

    def test_calculate_subscores(self):
        supplier = MagicMock(spec=Supplier)
        supplier.credit_terms = 45
        supplier.reliability_score = 0.8
        supplier.avg_delivery_days = 3
        
        scores = calculate_subscores(
            supplier=supplier,
            unit_price=100.0,
            avg_market_price=100.0,
            is_current_supplier=True,
            invoice_count=10
        )
        
        self.assertEqual(scores["credit_score"], 0.5)   # 45/90
        self.assertEqual(scores["price_score"], 0.5)    # Exact match
        self.assertEqual(scores["reliability_score"], 0.8)
        self.assertEqual(scores["switching_friction"], 1.0) # Current supplier
        # Delivery: 1 - (3-1)/13 = 1 - 2/13 = 1 - 0.1538 = 0.846
        self.assertTrue(0.8 < scores["delivery_speed"] < 0.9)


class TestAsyncIntelligenceEngine(unittest.IsolatedAsyncioTestCase):

    # ── Supplier Score Engine Tests ───────────────────────

    async def test_calculate_supplier_score(self):
        mock_db = AsyncMock()
        # Mock invoice count result. execute() returns a Result, scalar() returns value
        mock_result = MagicMock()
        mock_result.scalar.side_effect = [60] # Invoice count
        mock_db.execute.return_value = mock_result
        
        supplier = MagicMock(spec=Supplier)
        supplier.id = uuid4()
        supplier.avg_delivery_days = 1
        supplier.reliability_score = 0.6
        supplier.credit_terms = 90
        
        result = await calculate_supplier_score(supplier, mock_db)
        
        self.assertEqual(result["metrics"]["avg_delivery_days"], 1)
        self.assertEqual(result["breakdown"]["delivery_score"], 100) # 1 day = 100
        self.assertEqual(result["breakdown"]["credit_score"], 100)   # 90 days = 100
        
        # Reliability: Base 60 + Bonus 20 (capped) = 80
        self.assertEqual(result["breakdown"]["reliability_score"], 80)

    # ── Anomaly Detector Tests ────────────────────────────

    async def test_detect_anomalies(self):
        mock_db = AsyncMock()
        
        # Calls in detect_anomalies:
        # 1. New supplier check -> count query -> returns 0
        # 2. Market price check -> avg query -> returns 100.0
        # 3. Quantity check -> avg query -> returns 10.0
        
        # We need three separate mock results or one with side_effects on scalar/scalar_one
        # Let's mock the execute calls.
        
        # Mocking the Result object returned by execute
        mock_result_1 = MagicMock()
        mock_result_1.scalar.return_value = 0 # New supplier
        
        mock_result_2 = MagicMock()
        mock_result_2.scalar.return_value = 100.0 # Market Price
        
        mock_result_3 = MagicMock()
        mock_result_3.scalar.return_value = 10.0 # Avg Qty
        
        mock_db.execute.side_effect = [mock_result_1, mock_result_2, mock_result_3]
        
        item = MagicMock(spec=InvoiceItem)
        item.unit_price = 150.0  # +50% deviation (> 40%)
        item.quantity = 50       # 5x avg (> 3x)
        item.raw_description = "Test Item"
        item.product_id = uuid4()
        item.id = uuid4()
        
        score, flags = await detect_anomalies(
            mock_db, uuid4(), [item], uuid4(), uuid4()
        )
        
        self.assertIn("New Supplier", flags)
        self.assertTrue(any("Price Deviation" in f for f in flags))
        self.assertTrue(any("Quantity Spike" in f for f in flags))
        self.assertTrue(score > 60) # Sum of risks

if __name__ == '__main__':
    unittest.main()
