import json
import os

import edge_tts
from pocketflow import Node


class TTS(Node):
    def __init__(self):
        super().__init__()

    def prep(self, shared):
        print("=================Start processing TTS===================")
        return {
            "save_dir": shared["save_dir"],
            "save_file": "step_d.audio.mp3",
            "srt_file": "step_d.srt",
            "summary": shared['summary']
        }

    def exec(self, prep_res):
        # 准备文本
        summary_data = prep_res["summary"]
        tts_text = summary_data.get("summary", "")
        news_list = [f'{idx+1}. {item.get("title", "")}, {item.get("content", "")}' for idx, item in enumerate(summary_data.get("news", []))]
        # 如果只有一条新闻的话，那就不说总结了
        if len(news_list) == 1:
            tts_text = ''
        tts_text += "。".join(news_list)
        tts_text += summary_data.get("end", "")

        # 调用edge-tts
        communicate = edge_tts.Communicate(tts_text, "zh-CN-XiaoxiaoNeural")
        sub_maker = edge_tts.SubMaker()
        with open(os.path.join(prep_res["save_dir"], prep_res["save_file"]), "wb") as f:
            for chunk in communicate.stream_sync():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    sub_maker.feed(chunk)

        with open(os.path.join(prep_res["save_dir"], prep_res["srt_file"]), "w") as f:
            f.write(sub_maker.get_srt())

        return {
            "audio_path": os.path.join(prep_res["save_dir"], prep_res["save_file"]),
            "srt_path": os.path.join(prep_res["save_dir"], prep_res["srt_file"])
        }

    def post(self, shared, prep_res, exec_res):
        shared["audio_path"] = exec_res["audio_path"]
        shared["srt_path"] = exec_res["srt_path"]


if __name__ == '__main__':
    # ------ just for test -------
    from pocketflow import Flow
    shared_dict = {
        "save_dir": '../../data/20250621',
        "summary": json.loads(open('../../data/20250621/step_c.summary_news.json').read()),
    }
    tts = TTS()
    flow = Flow(start=tts)
    flow.run(shared_dict)
