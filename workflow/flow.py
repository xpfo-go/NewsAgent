from pocketflow import Flow

from workflow.nodes.cleaned import CleanedBBCNews
from workflow.nodes.fetch import FetchBBCNews
from workflow.nodes.movie import Movie
from workflow.nodes.summary import SummaryBBCNews
from workflow.nodes.tts import TTS
from workflow.nodes.raise_exception import RaiseException


def build_flow():
    fetch_news = FetchBBCNews(max_retries=5, wait=20)
    cleaned_news = CleanedBBCNews()
    summary_news = SummaryBBCNews()
    raise_exception = RaiseException()
    tts = TTS()
    movie = Movie()

    # 没有数据的话 则结束工作流
    fetch_news - "failed" >> raise_exception

    fetch_news >> cleaned_news
    cleaned_news >> summary_news

    # 总结失败提示
    summary_news - "failed" >> raise_exception

    summary_news >> tts >> movie
    flow = Flow(start=fetch_news)
    return flow

