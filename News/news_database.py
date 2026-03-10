import sqlite3

class NewsDatabase:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS news
            (id INTEGER PRIMARY KEY, title TEXT, link TEXT)
        """)
        self.conn.commit()

    def insert_news(self, title, link):
        self.cursor.execute("INSERT INTO news (title, link) VALUES (?, ?)", (title, link))
        self.conn.commit()

    def get_all_news(self):
        self.cursor.execute("SELECT * FROM news")
        return self.cursor.fetchall()

    def close_connection(self):
        self.conn.close()

def main():
    db = NewsDatabase("news.db")
    news_articles = collect_news("python programming")
    for article in news_articles:
        db.insert_news(article["title"], article["link"])
    db.close_connection()

def collect_news(query):
    import requests
    from bs4 import BeautifulSoup
    url = f"https://news.google.com/search?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")

    news_articles = []
    for article in soup.find_all("article"):
        title = article.find("h3").text.strip()
        link = article.find("a")["href"]
        news_articles.append({"title": title, "link": link})

    return news_articles

if __name__ == "__main__":
    main()
