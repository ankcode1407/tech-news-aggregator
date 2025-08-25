import os
import requests
from supabase import create_client, Client
from dotenv import load_dotenv

# Import the required libraries from Flask
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

# Load environment variables from .env file for local testing
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)

# Enable CORS (Cross-Origin Resource Sharing)
CORS(app)

# --- This is the function that was missing ---
# It contains the core logic for fetching and storing news.
def fetch_and_insert_news():
    """Fetches tech news from NewsAPI and inserts it into Supabase."""
    try:
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        news_api_key: str = os.environ.get("NEWS_API_KEY")

        if not all([url, key, news_api_key]):
            print("Error: Missing one or more required environment variables.")
            return False, "Missing environment variables"

        supabase: Client = create_client(url, key)
        
        print("Fetching news from NewsAPI...")
        response = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={
                "apiKey": news_api_key,
                "category": "technology",
                "language": "en"
            }
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
        
        return True, "Success"

    except Exception as e:
        print(f"An error occurred: {e}")
        return False, str(e)

# --- API Endpoints ---

@app.route("/")
def serve_index():
    """Serves the frontend index.html file from the current directory."""
    return send_from_directory('.', 'index.html')

@app.route("/api/articles", methods=["GET"])
def get_articles():
    """API endpoint for the frontend to fetch all stored articles."""
    try:
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        supabase: Client = create_client(url, key)
        
        # Fetch the 50 most recently published articles
        res = supabase.table("articles").select("*").order("published_at", desc=True).limit(50).execute()
        return jsonify(res.data), 200
    except Exception as e:
        print(f"Failed to fetch articles: {e}")
        return jsonify({"error": "Failed to retrieve articles."}), 500

@app.route("/api/news/fetch", methods=["POST"])
def trigger_news_fetch():
    """API endpoint to manually trigger the news fetching process."""
    success, message = fetch_and_insert_news()
    if success:
        return jsonify({"message": "News fetching logic executed successfully."}), 200
    else:
        return jsonify({"error": f"Failed to fetch and insert news: {message}"}), 500

# This block runs the Flask web server
if __name__ == "__main__":
    # The app will run on http://127.0.0.1:5000
    app.run(debug=True)
