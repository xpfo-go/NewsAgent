import unittest

from workflow.nodes.movie import select_video_codec


class MovieCodecTests(unittest.TestCase):
    def test_select_video_codec_for_darwin(self) -> None:
        self.assertEqual(select_video_codec("Darwin"), "h264_videotoolbox")

    def test_select_video_codec_for_linux(self) -> None:
        self.assertEqual(select_video_codec("Linux"), "libx264")

    def test_select_video_codec_for_windows(self) -> None:
        self.assertEqual(select_video_codec("Windows"), "libx264")


if __name__ == "__main__":
    unittest.main()
