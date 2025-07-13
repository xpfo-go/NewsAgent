import asyncio
import os
import sys
import time

import requests
from playwright.async_api import Playwright, async_playwright


class Douyin:
    def __init__(self, timeout: int, cookie_file: str, video_path: str):
        self.ua = {
            "web": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 "
                   "Safari/537.36",
            "app": "com.ss.android.ugc.aweme/110101 (Linux; U; Android 5.1.1; zh_CN; MI 9; Build/NMF26X; "
                   "Cronet/TTNetVersion:b4d74d15 2020-04-23 QuicVersion:0144d358 2020-03-24)"
        }

        self.timeout = timeout * 1000
        self.cookie_file = cookie_file

        self.video_path = video_path

    async def playwright_init(self, p: Playwright, headless=None):
        """
        初始化playwright
        """
        if headless is None:
            headless = False

        browser = await p.chromium.launch(headless=headless,
                                          chromium_sandbox=False,
                                          ignore_default_args=["--enable-automation"],
                                          channel="chrome"
                                          )
        return browser

    def get_web_userinfo(self, unique_id) -> str:
        """
        根据抖音号获取用户信息
        :param unique_id:
        :return:
        """
        url = "https://www.iesdouyin.com/web/api/v2/user/info/?unique_id={}".format(unique_id)
        res = requests.get(url, headers={"User-Agent": self.ua["web"]}).json()
        n = 0
        while True:
            n += 1
            try:
                nickname = res["user_info"]["nickname"]
                break
            except KeyError:
                print("获取用户昵称失败！")
            if n > 3:
                nickname = ''
                break
        return nickname

    async def upload(self, p: Playwright):
        browser = await self.playwright_init(p)
        context = await browser.new_context(storage_state=self.cookie_file, user_agent=self.ua["web"])
        page = await context.new_page()
        await page.add_init_script(path="runtime/stealth.min.js")
        await page.goto("https://creator.douyin.com/creator-micro/content/upload")
        print("正在判断账号是否登录")
        if "/creator-micro/" not in page.url:
            print("账号未登录")
            return
        print("账号已登录")

        try:

            # 上传视频
            try:
                # 1) 找到真正的上传按钮
                btn = page.locator('.container-drag-upload-tL99XD button')
                # 2) 监听 filechooser
                async with page.expect_file_chooser() as fc_info:
                    await btn.click()
                file_chooser = await fc_info.value
                # 3) 设置文件
                await file_chooser.set_files(self.video_path, timeout=self.timeout)
                print("文件上传成功！")
            except Exception as e:
                print("发布视频失败，可能网页加载失败了\n", e)

            # 等待跳转页面
            await page.wait_for_url(
                "https://creator.douyin.com/creator-micro/content/post/video?enter_from=publish_page")

            # css 选择器
            css_selector = ".zone-container"
            await page.locator(".ace-line > div").click()

            tag_index = 0
            # 只能添加5个热点话题
            video_desc_tag = [
                f'{time.strftime("%Y年%m月%d日", time.localtime())}最新消息！',
                '#国际',
                '#国际新闻',
                '#国际局势',
                '#咨询',
                '#国际热点新闻',
            ]
            for tag in video_desc_tag:
                await page.type(css_selector, tag)
                tag_index += 1
                await page.press(css_selector, "Space")
                print("正在添加第%s个话题" % tag_index)
            print("视频标题输入完毕，等待发布")

            # 循环获取点击按钮消息
            await asyncio.sleep(2)
            # 点击发布
            await page.get_by_role("button", name="发布", exact=True).click()
            try:
                # 等待跳转内容管理页面
                await page.wait_for_url(
                    "https://creator.douyin.com/creator-micro/content/manage*",
                    timeout=self.timeout
                )
                print("账号发布视频成功")
                is_while = False
                while True:
                    await asyncio.sleep(2)
                    msg = await page.locator('//*[@class="semi-toast-content-text"]').all_text_contents()
                    for msg_txt in msg:
                        print("来自网页的实时消息：" + msg_txt)
                        if msg_txt.find("发布成功") != -1:
                            is_while = True
                            print("账号发布视频成功")
                        elif msg_txt.find("上传成功") != -1:
                            try:
                                await page.locator('button.button--1SZwR:nth-child(1)').click()
                            except Exception as e:
                                print(e)
                                break
                            msg2 = await page.locator(
                                '//*[@class="semi-toast-content-text"]').all_text_contents()
                            for msg2_txt in msg2:
                                if msg2_txt.find("发布成功") != -1:
                                    is_while = True
                                    print("账号发布视频成功")
                                elif msg2_txt.find("已封禁") != -1:
                                    is_while = True
                                    print("账号视频发布功能已被封禁")
                        elif msg_txt.find("已封禁") != -1:
                            is_while = True
                            print("视频发布功能已被封禁")
                        elif msg_txt.find("作品上传中") != -1:
                            pass
                        elif msg_txt.find("发布失败") != -1:
                            is_while = True
                            print("发布失败")
                        else:
                            pass
                    if is_while:
                        break
            except Exception as e:
                print(e)

        except Exception as e:
            print("发布视频失败\n", e)
        finally:
            pass

    async def main(self):
        async with async_playwright() as playwright:
            await self.upload(playwright)
            print('end')


def run():
    cookie_path = 'runtime/cookie/cookie.json'

    today = time.strftime("%Y%m%d", time.localtime())

    target_dir = f'../data/{today}/'
    if not os.path.exists(target_dir) and not os.path.isdir(target_dir):
        print('今日还未生成视频，请先运行工作流。')
        sys.exit(0)
    video_path = f'../data/{today}/step_e.movie.mp4'
    print(video_path)

    app = Douyin(60, cookie_path, video_path)
    asyncio.run(app.main())


if __name__ == '__main__':
    run()
