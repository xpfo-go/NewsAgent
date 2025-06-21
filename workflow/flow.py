from pocketflow import Flow

from workflow.nodes.cleaned import CleanedBBCNews
from workflow.nodes.fetch import FetchBBCNews
from workflow.nodes.movie import Movie
from workflow.nodes.summary import SummaryBBCNews
from workflow.nodes.tts import TTS


def build_flow():
    fetch_news = FetchBBCNews(max_retries=5, wait=20)
    cleaned_news = CleanedBBCNews()
    summary_news = SummaryBBCNews()
    tts = TTS()
    movie = Movie()

    fetch_news >> cleaned_news
    cleaned_news >> summary_news
    # TODO 这里添加summary_news的循环
    summary_news >> tts >> movie
    flow = Flow(start=fetch_news)
    return flow

