import datetime
import json
import logging
import os

import requests
from bs4 import BeautifulSoup
from pocketflow import Node
from workflow.utils.logging import get_logger, log_event
from workflow.utils.retry import retry_call


class FetchBBCNews(Node):
    def __init__(self):
        super().__init__()
        self.logger = get_logger("newsagent.fetch")
        self.retry_attempts = int(os.getenv("NEWSAGENT_FETCH_RETRY_ATTEMPTS", "3"))
        self.retry_base_delay = float(os.getenv("NEWSAGENT_FETCH_RETRY_BASE_DELAY", "1"))
        self.retry_backoff = float(os.getenv("NEWSAGENT_FETCH_RETRY_BACKOFF", "2"))

    def prep(self, shared):
        log_event(self.logger, logging.INFO, "fetch.start")
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
        resp = self._request_with_retry(prep_res["bbc_news_url"], headers, "fetch.list")
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')

        scripts = soup.find_all('script')
        simorgh_found = False
        for script in scripts:
            if not (script.string and 'window.SIMORGH_DATA' in script.string):
                continue

            simorgh_found = True
            json_str = script.string[len('window.SIMORGH_DATA='):].rstrip(";")
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
                log_event(self.logger, logging.WARNING, "fetch.simorgh_decode_failed", error=str(e))
                continue

        if not simorgh_found:
            raise RuntimeError("SIMORGH_DATA script not found in BBC page.")

        log_event(self.logger, logging.INFO, "fetch.list_done", news_count=len(news_items))
        for item in news_items:
            link = item.get("link")
            if not link:
                continue
            try:
                resp = self._request_with_retry(link, headers, "fetch.detail")
            except Exception as exc:
                log_event(self.logger, logging.WARNING, "fetch.detail_failed", url=link, error=str(exc))
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
                log_event(self.logger, logging.WARNING, "fetch.detail_parse_failed", url=link, error=str(e))
                continue

        with open(os.path.join(prep_res["save_dir"], prep_res["save_file"]), "w", encoding="utf-8") as f:
            json.dump(news_items, f, indent=4, ensure_ascii=False)

        log_event(
            self.logger,
            logging.INFO,
            "fetch.finished",
            fetched=len(news_items),
            with_text=sum(1 for item in news_items if item.get("text")),
        )
        return {
            "news": news_items,
        }

    def post(self, shared, prep_res, exec_res):
        if len(exec_res["news"]) == 0:
            shared["error"] = "BBC News List is Empty."
            return "failed"
        shared["news"] = exec_res["news"]

    def _request_with_retry(self, url: str, headers: dict, operation: str) -> requests.Response:
        def _call() -> requests.Response:
            response = requests.get(url=url, headers=headers, timeout=10)
            response.raise_for_status()
            return response

        return retry_call(
            _call,
            attempts=self.retry_attempts,
            base_delay=self.retry_base_delay,
            backoff=self.retry_backoff,
            logger=self.logger,
            operation=operation,
        )


if __name__ == '__main__':
    from pocketflow import Flow
    shared_dict = {
        "save_dir": '../../data/20250720',
    }
    fetch = FetchBBCNews()
    flow = Flow(start=fetch)
    flow.run(shared_dict)
