class Project:
    def __init__(self, name, start_date, end_date):
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.tasks = []

    def add_task(self, task_name, start_date, end_date):
        self.tasks.append({
            'name': task_name,
            'start_date': start_date,
            'end_date': end_date
        })

    def print_project_details(self):
        print(f"Project Name: {self.name}")
        print(f"Start Date: {self.start_date}")
        print(f"End Date: {self.end_date}")
        print("Tasks:")
        for i, task in enumerate(self.tasks, start=1):
            print(f"{i}. {task['name']} - {task['start_date']} to {task['end_date']}")


def main():
    project_name = input("Enter project name: ")
    start_date = input("Enter start date (YYYY-MM-DD): ")
    end_date = input("Enter end date (YYYY-MM-DD): ")

    project = Project(project_name, start_date, end_date)

    while True:
        print("\nOptions:")
        print("1. Add task")
        print("2. Print project details")
        print("3. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            task_name = input("Enter task name: ")
            task_start_date = input("Enter task start date (YYYY-MM-DD): ")
            task_end_date = input("Enter task end date (YYYY-MM-DD): ")
            project.add_task(task_name, task_start_date, task_end_date)
        elif choice == "2":
            project.print_project_details()
        elif choice == "3":
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()