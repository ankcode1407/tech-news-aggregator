# File: fetch_script.py

import os
import requests
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables for local testing (GitHub Actions will provide them)
load_dotenv()

def fetch_and_insert_news():
    """Fetches tech news and inserts it into Supabase."""
    try:
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        news_api_key: str = os.environ.get("NEWS_API_KEY")

        if not all([url, key, news_api_key]):
            print("Error: Missing one or more required environment variables.")
            return

        supabase: Client = create_client(url, key)
        
        print("Fetching news from NewsAPI...")
        response = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={"apiKey": news_api_key, "category": "technology", "language": "en"}
        )
        response.raise_for_status()
        data = response.json()
        
        articles_to_insert = []
        for article in data.get("articles", []):
            if article.get("title") and article.get("url"):
                articles_to_insert.append({
                    "title": article["title"],
                    "source": article.get("source", {}).get("name"),
                    "url": article["url"],
                    "published_at": article["publishedAt"],
                    "category": "technology"
                })
        
        if articles_to_insert:
            print(f"Inserting/updating {len(articles_to_insert)} articles...")
            supabase.table("articles").upsert(articles_to_insert, on_conflict='url').execute()
            print("Successfully inserted/updated articles.")
        else:
            print("No new articles to insert.")

    except Exception as e:
        print(f"An error occurred: {e}")

# This makes the script runnable from the command line
if __name__ == "__main__":
    fetch_and_insert_news()