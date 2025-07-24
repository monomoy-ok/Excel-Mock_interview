# app/admin_ui.py

from app.question_bank import QUESTIONS


def list_questions():
    for level, qs in QUESTIONS.items():
        print(f"{level.title()}:")
        for i, q in enumerate(qs, 1):
            print(f"  {i}. {q}")


def add_question():
    level = input("Enter difficulty (basic/intermediate/advanced): ").strip().lower()
    question = input("Enter the new question: ").strip()
    if level in QUESTIONS:
        QUESTIONS[level].append(question)
        print("Question added.")
    else:
        print("Invalid level.")


def remove_question():
    level = input("Enter difficulty (basic/intermediate/advanced): ").strip().lower()
    if level in QUESTIONS:
        list_questions()
        idx = int(input("Enter question number to remove: ")) - 1
        if 0 <= idx < len(QUESTIONS[level]):
            removed = QUESTIONS[level].pop(idx)
            print(f"Removed: {removed}")
        else:
            print("Invalid number.")
    else:
        print("Invalid level.")


def admin_menu():
    while True:
        print("\nAdmin UI - Question Bank Management")
        print("1. List questions")
        print("2. Add question")
        print("3. Remove question")
        print("4. Exit")
        choice = input("Select an option: ").strip()
        if choice == "1":
            list_questions()
        elif choice == "2":
            add_question()
        elif choice == "3":
            remove_question()
        elif choice == "4":
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    admin_menu() 