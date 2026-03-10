import news_collector
import news_database
import news_gui

def main():
    while True:
        print("1. Collect news from Google News")
        print("2. Store news in database")
        print("3. Run news GUI")
        print("4. Quit")
        choice = input("Enter your choice: ")

        if choice == "1":
            news_collector.main()
        elif choice == "2":
            news_database.main()
        elif choice == "3":
            news_gui.main()
        elif choice == "4":
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
