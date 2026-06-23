import unittest

from app.config import settings
from app.services.llm_client import get_chat_model


class LlmClientTest(unittest.TestCase):
    def test_stage_model_falls_back_to_default(self):
        old_write = settings.llm_model_write
        old_default = settings.dashscope_model
        try:
            settings.llm_model_write = ""
            settings.dashscope_model = "default-model"
            self.assertEqual(get_chat_model("write"), "default-model")
        finally:
            settings.llm_model_write = old_write
            settings.dashscope_model = old_default

    def test_stage_model_override(self):
        old_write = settings.llm_model_write
        try:
            settings.llm_model_write = "writer-model"
            self.assertEqual(get_chat_model("write"), "writer-model")
        finally:
            settings.llm_model_write = old_write


if __name__ == "__main__":
    unittest.main()
