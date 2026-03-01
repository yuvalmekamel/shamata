from config import DB_PATH, MEVZAK_FEED_DISPLAY, MEVZAK_FEED_NAME, MEVZAK_FEED_URL
from db import init_db, save_articles
from fetcher import fetch_mevzakim


def main():
    print("=" * 60)
    print(f"  שמטה — מביא {MEVZAK_FEED_DISPLAY}")
    print("=" * 60)

    init_db(DB_PATH)

    articles = fetch_mevzakim(MEVZAK_FEED_URL, MEVZAK_FEED_NAME)
    print(f"\nנטענו {len(articles)} מבזקים מהפיד")

    new_count, duplicate_count = save_articles(articles, DB_PATH)
    print(f"נשמרו   {new_count} חדשים  |  דולגו {duplicate_count} כפולים\n")

    for i, article in enumerate(articles, start=1):
        date_str = (
            article.published_at.strftime("%d/%m/%Y %H:%M")
            if article.published_at
            else "תאריך לא ידוע"
        )
        print(f"{'─' * 60}")
        print(f"  [{i}] {article.title}")
        print(f"  {date_str}  |  {article.url}")

    print(f"\n{'─' * 60}")
    print(f"  סיום. מסד הנתונים: {DB_PATH}")


if __name__ == "__main__":
    main()
