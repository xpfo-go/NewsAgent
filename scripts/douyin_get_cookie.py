# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/10 22:11
@Author  : superhero
@Email   : 838210720@qq.com
@File    : get_cookie.py
@IDE: PyCharm
"""

import asyncio
import os
from playwright.async_api import Playwright, async_playwright


class creator_douyin():
    def __init__(self, timeout: int):
        """
        初始化
        :param phone: 手机号
        :param timeout: 你要等待多久，单位秒
        """
        self.timeout = timeout * 1000
        self.path = 'runtime'
        self.desc = "cookie.json"

        if not os.path.exists(os.path.join(self.path, "cookie")):
            os.makedirs(os.path.join(self.path, "cookie"))

    async def __cookie(self, playwright: Playwright) -> None:
        browser = await playwright.chromium.launch(channel="chrome", headless=False)

        context = await browser.new_context()

        page = await context.new_page()

        await page.add_init_script("Object.defineProperties(navigator, {webdriver:{get:()=>false}});")

        await page.goto("https://creator.douyin.com/")

        # 自动输入手机号 和勾选同意协议的，现在打开页面是扫码，先注释了
        # await page.locator(".agreement-FCwv7r > img:nth-child(1)").click()
        # await page.locator('#number').fill(self.phone)

        try:
            await page.wait_for_url("https://creator.douyin.com/creator-micro/home", timeout=self.timeout)
            cookies = await context.cookies()
            cookie_txt = ''
            for i in cookies:
                cookie_txt += i.get('name') + '=' + i.get('value') + '; '
            try:
                cookie_txt.index("sessionid")
                print("登录成功")
                await context.storage_state(path=os.path.join(self.path, "cookie", self.desc))
            except ValueError:
                print("登录失败，本次操作不保存cookie")
        except Exception as e:
            print("登录失败，本次操作不保存cookie", e)
        finally:
            await page.close()
            await context.close()
            await browser.close()

    async def main(self):
        async with async_playwright() as playwright:
            await self.__cookie(playwright)


def main():
    app = creator_douyin(60)
    asyncio.run(app.main())


if __name__ == '__main__':
    main()
