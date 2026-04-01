from pocketflow import Node


class RaiseException(Node):
    def prep(self, shared):
        return {
            "error": shared["error"]
        }

    def exec(self, prep_res):
        raise RuntimeError(prep_res["error"])

    def post(self, shared, prep_res, exec_res):
        pass
