import wikipedia
import json

def get_wikipedia_data(page_title):
    try:
        page = wikipedia.page(page_title)
        data = {
            "title": page.title,
            "url": page.url,
            "content": page.content
        }
        return data
    except wikipedia.exceptions.DisambiguationError as e:
        print(f"Disambiguation error: {e}")
        return None
    except wikipedia.exceptions.PageError as e:
        print(f"Page error: {e}")
        return None

def save_data_to_file(data, filename):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)

def main():
    page_title = "Python (programming language)"
    data = get_wikipedia_data(page_title)
    if data:
        filename = "wikipedia_data.json"
        save_data_to_file(data, filename)
        print(f"Data saved to {filename}")

if __name__ == "__main__":
    main()