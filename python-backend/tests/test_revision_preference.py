import unittest

from app.services.revision_preference import build_revision_preference


class RevisionPreferenceTest(unittest.TestCase):
    def test_detects_expansion_dialogue_and_bridge_changes(self):
        draft = "他推开门。\n\n走廊很黑。\n\n门关上了。"
        confirmed = (
            "他推开门，先听见门轴里压着的一声轻响。\n\n"
            "“别出声。”她说。\n\n"
            "走廊很黑，墙根的水痕一路延到楼梯口，他没有立刻往前走。\n\n"
            "门在身后关上，像有人替他合上了退路。"
        )

        result = build_revision_preference(draft, confirmed)

        self.assertGreater(result["lengthDelta"], 0)
        self.assertGreaterEqual(result["dialogueDelta"], 1)
        self.assertTrue(result["openingChanged"])
        self.assertTrue(result["endingChanged"])
        self.assertIn("rewrites_opening_bridge", result["signals"])
        self.assertIn("rewrites_ending_hook", result["signals"])


if __name__ == "__main__":
    unittest.main()
