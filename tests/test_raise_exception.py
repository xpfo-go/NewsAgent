import unittest

from workflow.nodes.raise_exception import RaiseException


class RaiseExceptionNodeTests(unittest.TestCase):
    def test_exec_raises_runtime_error(self) -> None:
        node = RaiseException()
        with self.assertRaises(RuntimeError):
            node.exec({"error": "boom"})


if __name__ == "__main__":
    unittest.main()
