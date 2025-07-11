import json
import os
import re
import shlex
import subprocess
from datetime import timedelta

from pocketflow import Node


class Movie(Node):
    def __init__(self):
        super().__init__()

    def prep(self, shared):
        print("=================Start gen Movie===================")
        return {
            "save_dir": shared["save_dir"],
            "save_file": "step_e.movie.mp4",
            "summary": shared['summary'],
            "audio_path": shared["audio_path"],
            "srt_path": shared["srt_path"],
            "font_path": shared["font_path"]
        }

    def exec(self, prep_res):
        # a. 提取标题
        structure = []
        for news in prep_res['summary']['news']:
            structure.append((news['title']))

        full_text = ''
        for i, section in enumerate(structure):
            full_text += f"{i + 1}. {section}\n"

        # b. 生成视频的一些配置参数
        video_size = (1920, 1080)
        font_size = 60
        output_path = os.path.join(prep_res["save_dir"], prep_res["save_file"])
        audio_path = prep_res["audio_path"]
        srt_path = prep_res["srt_path"]
        srt_path = self._format_srt(srt_path)

        ffprobe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ]
        result = subprocess.run(ffprobe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration = result.stdout.strip() or "10"  # 兜底 10s

        escaped_text = full_text

        # c. 构造 filter_complex
        font_path = prep_res["font_path"]
        font_name = os.path.splitext(os.path.basename(font_path))[0]

        filter_complex = (
            f"[0:v]drawtext="
            f"fontfile=‘{shlex.quote(font_path)}’:"
            f"text='{escaped_text}':"
            f"fontcolor=white:fontsize={font_size}:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:line_spacing=10,"
            f"subtitles={shlex.quote(srt_path)}:"
            f"force_style='FontName={font_name},FontSize=48,PrimaryColour=&HFFFFFF&,Alignment=2',"
            f"format=yuv420p[v]"
        )

        # d. 构建 ffmpeg 命令
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=0x0066cc:s={video_size[0]}x{video_size[1]}:d={duration}",
            "-i", audio_path,
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", "1:a",
            "-c:v", "h264_videotoolbox", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k", "-shortest",
            output_path
        ]

        # e. 执行
        subprocess.run(ffmpeg_cmd, check=True)

    def post(self, shared, prep_res, exec_res):
        print("success.")

    def _format_srt(self, srt_path):
        # 配置一下最小合并间隔，喘气停顿分割
        merge_gap = 0.23
        # 大于这这个字符则分割下一段，这里要兼容英文字幕。默认就挺好，改了分辨率效果不好的话再来调这边。
        # 中文的长度的话用下面时间控制，两秒大概能说十来个字吧 不到15个字。
        # 还是不放心的话把字幕的字体调小点
        min_chars = 20
        # 这个控制字幕合并
        min_duration = 2.0

        # 先读取原始rst 然后转换为python的列表对象
        with open(srt_path, encoding='utf-8') as f:
            content = f.read().strip()

        raw_entries = []
        for block in re.split(r'\n\s*\n', content):
            lines = block.splitlines()
            if len(lines) >= 3:
                times = lines[1]
                text = ''.join(lines[2:])
                m = re.match(
                    r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})',
                    times
                )
                if m:
                    raw_entries.append({
                        'start': self.to_timedelta(m.group(1)),
                        'end': self.to_timedelta(m.group(2)),
                        'text': text
                    })

        # 下面是按 merge_gap 分割了，prelim_groups 则是二维数组，第二维这里不应该合并，所以存了源数据。
        # 合并的话会导致 min_chars 分割不出来，等到下面再合并
        prelim_groups = []
        current_group = []
        for entry in raw_entries:
            if not current_group:
                current_group.append(entry)
            else:
                prev = current_group[-1]
                gap = (entry['start'] - prev['end']).total_seconds()
                if gap < merge_gap:
                    # 同一簇，继续添加
                    current_group.append(entry)
                else:
                    # 新簇开始
                    prelim_groups.append(current_group)
                    current_group = [entry]
        if current_group:
            prelim_groups.append(current_group)

        # 按 merge_gap 分割之后就是按 min_chars, min_duration 分割合并了
        merged = []
        for group in prelim_groups:
            buf_text = []
            buf_start = None
            buf_end = None

            def flush():
                nonlocal buf_text, buf_start, buf_end
                if buf_text:
                    merged.append((buf_start, buf_end, ''.join(buf_text)))
                buf_text = []
                buf_start = buf_end = None

            for entry in group:
                if buf_start is None:
                    buf_start = entry['start']
                buf_end = entry['end']
                buf_text.append(entry['text'])

                span = (buf_end - buf_start).total_seconds()
                chars = len(''.join(buf_text))

                if chars >= min_chars or span >= min_duration:
                    flush()

            # 每个簇结束后 flush 剩余
            flush()

        # 将srt_path的文件名改一下，然后保存
        out_path = os.path.splitext(srt_path)[0] + '_formatted.srt'
        with open(out_path, 'w', encoding='utf-8') as f:
            for i, (start, end, text) in enumerate(merged, start=1):
                f.write(f"{i}\n")
                f.write(f"{self.to_timestamp(start)} --> {self.to_timestamp(end)}\n")
                f.write(text + "\n\n")
        return out_path

    @staticmethod
    def to_timedelta(ts):
        """把 'HH:MM:SS,mmm' 转为 timedelta"""
        h, m, s_ms = ts.split(':')
        s, ms = s_ms.split(',')
        return timedelta(hours=int(h), minutes=int(m), seconds=int(s), milliseconds=int(ms))

    @staticmethod
    def to_timestamp(td):
        """把 timedelta 转为 'HH:MM:SS,mmm'"""
        total_ms = int(td.total_seconds() * 1000)
        ms = total_ms % 1000
        s = (total_ms // 1000) % 60
        m = (total_ms // 60000) % 60
        h = total_ms // 3600000
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


if __name__ == '__main__':
    # ------ just for test -------
    from pocketflow import Flow

    shared_dict = {
        "save_dir": '../../data/20250621',
        "summary": json.loads(open('../../data/20250621/step_c.summary_news.json').read()),
        "audio_path": r'../../data/20250621/step_d.audio.mp3',
        "srt_path": '../../data/20250621/step_d.srt',
        "font_path": '/System/Library/Fonts/STHeiti Light.ttc'
    }
    movie = Movie()
    # movie._format_srt(shared_dict["srt_path"])
    flow = Flow(start=movie)
    flow.run(shared_dict)
