import tkinter as tk
from tkinter import ttk
from news_collector import collect_news

class NewsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("News Collector")
        self.query = tk.StringVar()

        self.query_label = tk.Label(root, text="Enter a query to search for news:")
        self.query_label.pack()

        self.query_entry = tk.Entry(root, textvariable=self.query)
        self.query_entry.pack()

        self.search_button = tk.Button(root, text="Search", command=self.search_news)
        self.search_button.pack()

        self.news_frame = tk.Frame(root)
        self.news_frame.pack()

    def search_news(self):
        query = self.query.get()
        news_articles = collect_news(query)
        for widget in self.news_frame.winfo_children():
            widget.destroy()

        for article in news_articles:
            article_frame = tk.Frame(self.news_frame)
            article_frame.pack(fill="x")

            title_label = tk.Label(article_frame, text=article["title"])
            title_label.pack()

            link_label = tk.Label(article_frame, text=article["link"])
            link_label.pack()

            separator = tk.Frame(article_frame, height=1, bg="gray")
            separator.pack(fill="x")

if __name__ == "__main__":
    root = tk.Tk()
    gui = NewsGUI(root)
    root.mainloop()
