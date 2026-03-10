import requests
from bs4 import BeautifulSoup

def get_news():
    """
    Retrieves and prints the latest news headlines from Google News.
    """
    url = "https://news.google.com/topstories?hl=en-US&gl=US&ceid=US:en"
    
    try:
        response = requests.get(url, timeout=5)  # Set a timeout of 5 seconds
        response.raise_for_status()  # Raise an exception for HTTP errors
    except requests.RequestException as e:
        print(f"Error retrieving news: {e}")
        return
    
    try:
        soup = BeautifulSoup(response.text, 'lxml')  # Use lxml parser
        news_headlines = soup.select('h3.ipQwMb.ekueJc.RD0gLb')  # Use CSS selector
        
        if not news_headlines:
            print("No news headlines found.")
            return
        
        for i, headline in enumerate(news_headlines, start=1):  # Start index from 1
            print(f"News {i}: {headline.text.strip()}")
    
    except Exception as e:
        print(f"Error parsing news: {e}")

if __name__ == "__main__":
    get_news()