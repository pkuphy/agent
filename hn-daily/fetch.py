#!/usr/bin/env python3
"""Fetch HackerNews Top 30 and summarize with Kimi API."""

import asyncio
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import httpx
from jinja2 import Environment, FileSystemLoader

HN_TOP_URL = "https://hacker-news.firebaseio.com/v1/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v1/item/{}.json"
KIMI_API_URL = "https://api.moonshot.cn/v1/chat/completions"
KIMI_MODEL = "kimi-k2.5"
TOP_N = 30
CONCURRENCY = 5

MOONSHOT_API_KEY = os.environ.get("MOONSHOT_API_KEY", "")


async def fetch_top_ids(client: httpx.AsyncClient) -> list[int]:
    resp = await client.get(HN_TOP_URL)
    resp.raise_for_status()
    return resp.json()[:TOP_N]


async def fetch_item(client: httpx.AsyncClient, item_id: int) -> dict:
    resp = await client.get(HN_ITEM_URL.format(item_id))
    resp.raise_for_status()
    return resp.json()


async def summarize(client: httpx.AsyncClient, sem: asyncio.Semaphore, story: dict) -> str:
    title = story.get("title", "")
    url = story.get("url", f"https://news.ycombinator.com/item?id={story['id']}")

    prompt = (
        f"请用一句话（不超过50字）概括这篇文章的主题和价值：\n"
        f"标题：{title}\n"
        f"链接：{url}"
    )

    payload = {
        "model": KIMI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.6,
        "max_tokens": 100,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MOONSHOT_API_KEY}",
    }

    async with sem:
        try:
            resp = await client.post(KIMI_API_URL, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"  Warning: summarize failed for {title!r}: {e}", file=sys.stderr)
            return ""


async def main():
    if not MOONSHOT_API_KEY:
        print("Error: MOONSHOT_API_KEY is not set", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(__file__).parent / "output"
    archive_dir = output_dir / "archive"
    output_dir.mkdir(exist_ok=True)
    archive_dir.mkdir(exist_ok=True)

    today = date.today()
    today_str = today.isoformat()
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    print(f"Fetching HN top {TOP_N}...")
    async with httpx.AsyncClient() as client:
        ids = await fetch_top_ids(client)

        print("Fetching story details...")
        stories = await asyncio.gather(*[fetch_item(client, i) for i in ids])
        stories = [s for s in stories if s and s.get("title")]

        print("Summarizing with Kimi...")
        sem = asyncio.Semaphore(CONCURRENCY)
        summaries = await asyncio.gather(*[summarize(client, sem, s) for s in stories])

    items = []
    for story, summary in zip(stories, summaries):
        items.append({
            "id": story["id"],
            "title": story.get("title", ""),
            "url": story.get("url", f"https://news.ycombinator.com/item?id={story['id']}"),
            "hn_url": f"https://news.ycombinator.com/item?id={story['id']}",
            "score": story.get("score", 0),
            "comments": story.get("descendants", 0),
            "summary": summary,
        })

    # Collect archive list
    archive_files = sorted(archive_dir.glob("*.html"), reverse=True)
    archive_dates = [f.stem for f in archive_files]

    env = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"))
    tmpl = env.get_template("index.html")

    html = tmpl.render(
        items=items,
        today=today_str,
        generated_at=generated_at,
        archive_dates=archive_dates,
    )

    # Write today's archive
    (archive_dir / f"{today_str}.html").write_text(html, encoding="utf-8")
    # Write index
    (output_dir / "index.html").write_text(html, encoding="utf-8")

    print(f"Done. Output: {output_dir}/index.html")


if __name__ == "__main__":
    asyncio.run(main())
