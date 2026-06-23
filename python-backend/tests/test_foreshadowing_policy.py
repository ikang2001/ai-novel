import unittest

from app.services.foreshadowing_service import ForeshadowingService


class ForeshadowingPolicyTest(unittest.TestCase):
    def test_default_thresholds_by_importance(self):
        self.assertEqual(ForeshadowingService._threshold_for_importance(5), 8)
        self.assertEqual(ForeshadowingService._threshold_for_importance(4), 10)
        self.assertEqual(ForeshadowingService._threshold_for_importance(3), 14)

    def test_custom_threshold_overrides_default(self):
        policy = {"importanceThresholds": {"5": 6, "4": 9, "default": 12}}
        self.assertEqual(ForeshadowingService._threshold_for_importance(5, policy), 6)
        self.assertEqual(ForeshadowingService._threshold_for_importance(4, policy), 9)
        self.assertEqual(ForeshadowingService._threshold_for_importance(2, policy), 12)


if __name__ == "__main__":
    unittest.main()
