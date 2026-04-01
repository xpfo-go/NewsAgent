import json
import tempfile
import unittest

from workflow.nodes.summary import SummaryBBCNews


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("temporary openai error")
        payload = {"summary": "s", "news": [{"title": "t", "content": "c"}], "end": "e"}
        return _FakeResponse(json.dumps(payload, ensure_ascii=False))


class _FakeChat:
    def __init__(self, completions: _FakeCompletions) -> None:
        self.completions = completions


class _FakeClient:
    def __init__(self) -> None:
        self._completions = _FakeCompletions()
        self.chat = _FakeChat(self._completions)

    @property
    def calls(self) -> int:
        return self._completions.calls


class SummaryRetryTests(unittest.TestCase):
    def test_summary_exec_retries_on_transient_error(self) -> None:
        client = _FakeClient()
        node = SummaryBBCNews(client=client, model="test-model")
        node.retry_base_delay = 0
        with tempfile.TemporaryDirectory() as tmp:
            prep = {
                "save_dir": tmp,
                "save_file": "step_c.summary_news.json",
                "cleaned_news": [{"title": "n", "content": "x"}],
            }
            result = node.exec(prep)

            self.assertTrue(result["ok"])
            self.assertEqual(client.calls, 2)


if __name__ == "__main__":
    unittest.main()
