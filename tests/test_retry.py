import unittest

from workflow.utils.retry import retry_call


class RetryCallTests(unittest.TestCase):
    def test_retry_call_retries_then_success(self) -> None:
        attempts = {"n": 0}

        def flaky() -> str:
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise RuntimeError("transient")
            return "ok"

        out = retry_call(flaky, attempts=3, base_delay=0, sleep=lambda _: None)
        self.assertEqual(out, "ok")
        self.assertEqual(attempts["n"], 3)

    def test_retry_call_raises_after_max_attempts(self) -> None:
        attempts = {"n": 0}

        def always_fail() -> None:
            attempts["n"] += 1
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            retry_call(always_fail, attempts=2, base_delay=0, sleep=lambda _: None)
        self.assertEqual(attempts["n"], 2)


if __name__ == "__main__":
    unittest.main()
