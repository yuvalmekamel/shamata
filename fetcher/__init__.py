import hashlib
import html
import re
import ssl
import urllib.request
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

import certifi
import feedparser


def _ssl_handler() -> urllib.request.HTTPSHandler:
    """Return an HTTPS handler that uses certifi's CA bundle."""
    ctx = ssl.create_default_context(cafile=certifi.where())
    return urllib.request.HTTPSHandler(context=ctx)


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode HTML entities from a string."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _make_guid(entry) -> str:
    """Return the RSS guid, or a stable hash of the URL as fallback."""
    if entry.get("id"):
        return entry["id"].strip()
    url = entry.get("link", "")
    return hashlib.sha1(url.encode()).hexdigest()


def _parse_date(entry) -> Optional[datetime]:
    """Return a timezone-aware datetime from a feedparser entry, or None."""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
    return None


@dataclass
class Article:
    guid: str
    title: str
    url: str
    summary: str
    published_at: Optional[datetime]
    source: str


def fetch_mevzakim(feed_url: str, feed_name: str) -> list[Article]:
    """
    Fetch the Ynet מבזקים RSS feed.
    Returns a deduplicated list of Article objects, newest first.
    """
    parsed = feedparser.parse(feed_url, handlers=[_ssl_handler()])

    if parsed.bozo and not parsed.entries:
        print(f"  [אזהרה] שגיאה בטעינת הפיד '{feed_name}': {parsed.bozo_exception}")
        return []

    articles: list[Article] = []
    seen_guids: set[str] = set()

    for entry in parsed.entries:
        title = _strip_html(entry.get("title", "")).strip()
        url = entry.get("link", "").strip()

        if not title or not url:
            continue

        guid = _make_guid(entry)
        if guid in seen_guids:
            continue
        seen_guids.add(guid)

        # מבזקים often have no description, or it duplicates the title.
        # Use whichever of description/title is longer as the summary.
        raw_summary = _strip_html(entry.get("summary", entry.get("description", "")))
        summary = raw_summary if len(raw_summary) > len(title) else title

        articles.append(
            Article(
                guid=guid,
                title=title,
                url=url,
                summary=summary,
                published_at=_parse_date(entry),
                source=feed_name,
            )
        )

    return articles
