import argparse
import datetime
import os
from pathlib import Path

import dotenv

from workflow.flow import build_flow


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SAVE_DIR = ROOT_DIR / "data"


dotenv.load_dotenv(ROOT_DIR / ".env")


def main():
    parser = argparse.ArgumentParser(description="Generate daily BBC Chinese news report.")
    parser.add_argument(
        "-dir",
        "--save_dir",
        default=str(DEFAULT_SAVE_DIR),
        help="Save workflow data directory for output (default: ./data).",
    )
    parser.add_argument("-font", "--font_path", default="/System/Library/Fonts/STHeiti Light.ttc",
                        help="News video font.")
    args = parser.parse_args()

    cur_save_dir = Path(args.save_dir) / datetime.datetime.now().strftime("%Y%m%d")
    cur_save_dir.mkdir(parents=True, exist_ok=True)

    shared = {
        "save_dir": str(cur_save_dir),
        "font_path": args.font_path
    }

    flow = build_flow()
    flow.run(shared)


if __name__ == '__main__':
    main()
