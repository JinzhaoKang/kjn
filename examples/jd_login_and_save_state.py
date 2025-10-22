#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
先登录京东并把浏览器状态保存下来（供爬虫复用）
用法：
  PYTHONPATH=$(pwd) python3 examples/jd_login_and_save_state.py --out examples/jd_state.json
"""

import asyncio
import argparse
from pathlib import Path

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="examples/jd_state.json", help="保存的 Playwright storage_state 路径")
    ap.add_argument("--ua", default="", help="可选：自定义 User-Agent")
    args = ap.parse_args()

    from playwright.async_api import async_playwright

    state_path = Path(args.out).resolve()
    state_path.parent.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        # 可视化窗口，扫码更方便
        browser = await pw.chromium.launch(headless=False)
        context_kwargs = {}
        if args.ua:
            context_kwargs["user_agent"] = args.ua
        ctx = await browser.new_context(**context_kwargs)

        page = await ctx.new_page()
        await page.goto("https://passport.jd.com/new/login.aspx")
        print("请在弹出的浏览器里登录（建议手机扫码）。登录成功后我会保存状态。")

        # 给足够时间扫码 + 等待登录完成
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(15000)

        # 随便打开主页，确认登录有效
        try:
            await page.goto("https://www.jd.com", wait_until="networkidle")
        except Exception:
            pass

        await ctx.storage_state(path=str(state_path))
        print(f"[OK] 已保存状态到: {state_path}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
