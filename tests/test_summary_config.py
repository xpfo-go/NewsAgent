import unittest
from unittest.mock import patch

from workflow.nodes.summary import resolve_openai_config


class SummaryConfigTests(unittest.TestCase):
    @patch.dict("os.environ", {}, clear=True)
    def test_resolve_openai_config_requires_env(self) -> None:
        with self.assertRaises(ValueError):
            resolve_openai_config()

    @patch.dict(
        "os.environ",
        {
            "OPENAI_API_KEY": "k",
            "OPENAI_BASE_URL": "https://example.com/v1",
            "OPENAI_MODEL": "gpt-test",
        },
        clear=True,
    )
    def test_resolve_openai_config_success(self) -> None:
        cfg = resolve_openai_config()
        self.assertEqual(cfg.api_key, "k")
        self.assertEqual(cfg.base_url, "https://example.com/v1")
        self.assertEqual(cfg.model, "gpt-test")


if __name__ == "__main__":
    unittest.main()
