import requests
from bs4 import BeautifulSoup

def collect_news(query):
    """
    Collect news from Google News based on the given query.
    """
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

def main():
    query = input("Enter a query to search for news: ")
    news_articles = collect_news(query)
    for article in news_articles:
        print(f"Title: {article['title']}")
        print(f"Link: {article['link']}")
        print("------------------------")

if __name__ == "__main__":
    main()
