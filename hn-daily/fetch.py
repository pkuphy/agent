#!/usr/bin/env python3
"""Fetch HackerNews Top 30 and summarize with Kimi API."""

import asyncio
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import httpx
from jinja2 import Environment, FileSystemLoader

HN_ALGOLIA_URL = "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage={n}"
KIMI_API_URL = "https://api.moonshot.cn/v1/chat/completions"
KIMI_MODEL = "kimi-k2.5"
TOP_N = 30
CONCURRENCY = 5

MOONSHOT_API_KEY = os.environ.get("MOONSHOT_API_KEY", "")


async def fetch_top_stories(client: httpx.AsyncClient) -> list[dict]:
    resp = await client.get(HN_ALGOLIA_URL.format(n=TOP_N))
    resp.raise_for_status()
    hits = resp.json().get("hits", [])
    return [
        {
            "id": h.get("objectID", ""),
            "title": h.get("title", ""),
            "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
            "score": h.get("points", 0),
            "comments": h.get("num_comments", 0),
        }
        for h in hits
        if h.get("title")
    ]


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
            if resp.status_code != 200:
                print(f"  Warning: summarize failed for {title!r}: {resp.status_code} {resp.text}", file=sys.stderr)
                return ""
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
        stories = await fetch_top_stories(client)

        print("Summarizing with Kimi...")
        sem = asyncio.Semaphore(CONCURRENCY)
        summaries = await asyncio.gather(*[summarize(client, sem, s) for s in stories])

    items = []
    for story, summary in zip(stories, summaries):
        items.append({
            **story,
            "hn_url": f"https://news.ycombinator.com/item?id={story['id']}",
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
