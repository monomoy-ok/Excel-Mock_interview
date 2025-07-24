# app/question_bank.py

import random

# Sample Excel interview questions
QUESTIONS = {
    "basic": [
        "How do you use the VLOOKUP function in Excel?",
        "What is the difference between relative and absolute cell references?",
        "Explain how you would use conditional formatting."
        "how can we use data formatting in excel?"
        "what is the difference between a formula and a function in excel?" 
        
    ],
    "intermediate": [
        "How do you create and use pivot tables?",
        "What are named ranges and how are they useful?",
        "Explain how to use the INDEX and MATCH functions together."
    ],
    "advanced": [
        "How would you automate a report in Excel using VBA?",
        "Describe a scenario where Power Query helped you clean complex data.",
        "How can you use dynamic arrays in Excel to analyze data?"
    ]
}


def get_random_questions(n=3):
    """
    Return a mixed list of basic, intermediate, and advanced questions.
    """
    q1 = random.choice(QUESTIONS["basic"])
    q2 = random.choice(QUESTIONS["intermediate"])
    q3 = random.choice(QUESTIONS["advanced"])
    return [q1, q2, q3][:n]


def get_question_by_difficulty(level):
    """
    Return a random question from the specified difficulty level.
    """
    import random
    if level not in QUESTIONS:
        level = 'basic'
    return random.choice(QUESTIONS[level])
