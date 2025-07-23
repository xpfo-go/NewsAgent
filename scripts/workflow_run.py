import argparse
import datetime
import os

import dotenv

from workflow.flow import build_flow


dotenv.load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Generate Hacker News report.")
    parser.add_argument("-dir", "--save_dir", default="../data",
                        help="Save workflow data directory for output (default: ./data).")
    parser.add_argument("-font", "--font_path", default="/System/Library/Fonts/STHeiti Light.ttc",
                        help="News video font.")
    args = parser.parse_args()

    cur_save_dir = os.path.join(args.save_dir, datetime.datetime.now().strftime("%Y%m%d"))
    if not os.path.exists(cur_save_dir):
        os.makedirs(cur_save_dir)

    shared = {
        "save_dir": cur_save_dir,
        "font_path": args.font_path
    }

    flow = build_flow()
    flow.run(shared)


if __name__ == '__main__':
    main()
