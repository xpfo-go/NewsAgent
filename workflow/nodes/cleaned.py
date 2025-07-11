import os
import json
from pocketflow import Node


class CleanedBBCNews(Node):
    def prep(self, shared):
        print("=================Start cleaning BBC News===================")
        return {
            "save_dir": shared["save_dir"],
            "save_file": "step_b.cleaned_news.json",
            "news": shared['news']
        }

    def exec(self, prep_res):
        news_items = prep_res["news"]
        cleaned_news = []

        for item in news_items:
            cleaned_item = {
                "title": item.get("title"),
                "content": item.get("text"),
            }
            cleaned_news.append(cleaned_item)

        with open(os.path.join(prep_res["save_dir"], prep_res["save_file"]), "w") as f:
            json.dump(cleaned_news, f, indent=4, ensure_ascii=False)

        return {
            "cleaned_news": cleaned_news
        }

    def post(self, shared, prep_res, exec_res):
        shared["cleaned_news"] = exec_res["cleaned_news"]


if __name__ == '__main__':
    from pocketflow import Flow
    shared_dict = {
        "save_dir": '../../data/20250621',
        "news": json.loads(open('../../data/20250621/step_a.fetch_news.json').read())
    }
    cleaned = CleanedBBCNews()
    flow = Flow(start=cleaned)
    flow.run(shared_dict)
