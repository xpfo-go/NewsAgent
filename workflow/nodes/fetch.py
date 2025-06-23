import datetime
import os
import re

import requests
import json
import time

from bs4 import BeautifulSoup
from pocketflow import Node


class FetchBBCNews(Node):
    def prep(self, shared):
        print("=================Start Fetch BBC News===================")
        return {
            "bbc_news_url": "https://www.bbc.com/zhongwen/topics/c83plve5vmjt/simp",
            "save_dir": shared["save_dir"],
            "save_file": "step_a.fetch_news.json"
        }

    def exec(self, prep_res):
        news_items = []

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        }
        resp = requests.get(
            url=prep_res["bbc_news_url"],
            headers=headers,
            timeout=10
        )
        resp.raise_for_status()
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')

        scripts = soup.find_all('script')
        for script in scripts:
            if not (script.string and 'window.SIMORGH_DATA' in script.string):
                continue

            json_str = script.string[len('window.SIMORGH_DATA='):]
            try:
                raw_data = json.loads(json_str)
                curations_list = raw_data.get('pageData', {}).get('curations', [])
                if len(curations_list) > 0:
                    curation = curations_list[0]
                    result_items = curation.get('summaries', [])

                    one_day_ago = datetime.datetime.now() - datetime.timedelta(hours=24)
                    for item in result_items:
                        time_format = "%Y-%m-%dT%H:%M:%S.%fZ"
                        published_utc_time = datetime.datetime.strptime(item["lastPublished"], time_format)
                        published_shanghai_time = published_utc_time + datetime.timedelta(hours=8)

                        if published_shanghai_time < one_day_ago:
                            continue
                        item["time"] = published_shanghai_time.strftime("%Y-%m-%d %H:%M:%S")
                        news_items.append(item)

                break
            except json.JSONDecodeError as e:
                raise AssertionError(f"JSON decode error: {e}")

        print("Fetch BBC News List Successfully. Now Start Fetch BBC News Detail.....")
        for item in news_items:
            resp = requests.get(
                url=item["link"],
                headers=headers,
                timeout=10
            )
            if not resp.ok:
                continue

            html = resp.text
            try:
                soup = BeautifulSoup(html, 'html.parser')
                text_list = [item.get_text(strip=True) for item in soup.find_all('p', class_='e17g058b0')]
                if len(text_list) == 0:
                    continue
                text = '\n'.join(text_list)
                item["text"] = text
            except Exception as e:
                print(f"Failed to parse BBC News Detail: {e}")
                continue

        with open(os.path.join(prep_res["save_dir"], prep_res["save_file"]), "w") as f:
            json.dump(news_items, f, indent=4, ensure_ascii=False)

        return {
            "news": news_items,
        }

    def post(self, shared, prep_res, exec_res):
        shared["news"] = exec_res["news"]


if __name__ == '__main__':
    from pocketflow import Flow
    shared_dict = {
        "save_dir": '../../data/20250621',
    }
    fetch = FetchBBCNews()
    flow = Flow(start=fetch)
    flow.run(shared_dict)
