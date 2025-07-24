import pandas as pd
import random

subjects = ['Python', 'Data Structures', 'OOP', 'Machine Learning']
difficulties = ['beginner', 'intermediate', 'advanced']
learning_styles = ['visual', 'auditory', 'kinesthetic']
skill_levels = ['beginner', 'intermediate', 'advanced']

rows = []
for user_id in range(1, 1001):
    for _ in range(random.randint(3, 7)):  # Each student takes 3-7 quizzes
        subject = random.choice(subjects)
        difficulty = random.choice(difficulties)
        score = random.randint(40, 100)
        time_spent = random.randint(60, 300)  # seconds
        learning_style = random.choice(learning_styles)
        skill_level = random.choice(skill_levels)
        rows.append({
            'user_id': user_id,
            'subject': subject,
            'difficulty': difficulty,
            'score': score,
            'time_spent': time_spent,
            'learning_style': learning_style,
            'skill_level': skill_level
        })

# Save to CSV
pd.DataFrame(rows).to_csv('student_quiz_data.csv', index=False)

print('Generated student_quiz_data.csv with 1000 students.') 