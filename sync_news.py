#!/usr/bin/env python3
"""Keep the News list on index.html capped at N items, moving overflow into
news.html's archive.

Usage:
    ./sync_news.py           # cap index.html's News list at 8 items (default)
    ./sync_news.py --max 5   # use a different cap
    ./sync_news.py --check   # exit 1 if index.html has more than the cap, change nothing

Both lists are newest-first, so overflow items are removed from the bottom of
index.html's list and inserted at the top of news.html's list, in the same
relative order.
"""
import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
INDEX_HTML = REPO_ROOT / "index.html"
NEWS_HTML = REPO_ROOT / "news.html"

LI_RE = re.compile(r"<li>.*?</li>", re.DOTALL)
INDEX_LIST_RE = re.compile(
    r"(<h2>News \(<a href=\"news\.html\">Archived News</a>\)</h2>\s*<ul>\n)(.*?)(\n</ul>)",
    re.DOTALL,
)
NEWS_LIST_RE = re.compile(
    r"(<h1>Archived News</h1>\s*</div>\s*<ul>\n)(.*?)(\n</ul>)",
    re.DOTALL,
)


def split_items(block: str) -> list[str]:
    return LI_RE.findall(block)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max", type=int, default=8, help="max items to keep on index.html (default: 8)")
    parser.add_argument("--check", action="store_true", help="report only, exit 1 if a sync is needed")
    args = parser.parse_args()

    index_text = INDEX_HTML.read_text()
    news_text = NEWS_HTML.read_text()

    index_match = INDEX_LIST_RE.search(index_text)
    news_match = NEWS_LIST_RE.search(news_text)
    if not index_match or not news_match:
        print("error: could not locate the News list in index.html or news.html", file=sys.stderr)
        return 2

    index_items = split_items(index_match.group(2))
    if len(index_items) <= args.max:
        print(f"index.html has {len(index_items)} item(s), at or under the cap of {args.max}. Nothing to do.")
        return 0

    keep, overflow = index_items[: args.max], index_items[args.max :]

    if args.check:
        print(f"index.html has {len(index_items)} item(s), over the cap of {args.max} by {len(overflow)}.")
        return 1

    news_items = split_items(news_match.group(2))
    new_news_items = overflow + news_items

    new_index_block = "\n".join(keep)
    new_news_block = "\n".join(new_news_items)

    index_text = index_text[: index_match.start()] + index_match.group(1) + new_index_block + index_match.group(3) + index_text[index_match.end() :]
    news_text = news_text[: news_match.start()] + news_match.group(1) + new_news_block + news_match.group(3) + news_text[news_match.end() :]

    INDEX_HTML.write_text(index_text)
    NEWS_HTML.write_text(news_text)

    print(f"Moved {len(overflow)} item(s) from index.html to the top of news.html's archive.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
