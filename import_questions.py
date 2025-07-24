import csv
import json
from app import app, db
from models import QuizQuestion, Content

CSV_FILE = 'real_questions.csv'

with app.app_context():
    # Remove all existing questions
    QuizQuestion.query.delete()
    db.session.commit()

    # Get all unique subjects from the CSV
    subjects = set()
    with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            subjects.add(row['subject'])
    # Create content entries for each subject if not exist
    content_map = {}
    for subject in subjects:
        content = Content.query.filter_by(title=subject).first()
        if not content:
            content = Content(
                title=subject,
                description=f"Content for {subject}",
                content_type='article',
                difficulty_level='beginner',
                subject=subject,
                tags=json.dumps([subject.lower()])
            )
            db.session.add(content)
            db.session.commit()
            content_map[subject] = content.id
        else:
            content_map[subject] = content.id
    # Insert questions
    with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if not row.get('correct_answer') or not row['correct_answer'].strip():
                print(f"Skipping row with missing correct_answer: {row}")
                continue
            options = [row['option_a'], row['option_b'], row['option_c'], row['option_d']]
            question = QuizQuestion(
                content_id=content_map[row['subject']],
                question_text=row['question_text'],
                options=json.dumps(options),
                correct_answer=row['correct_answer'],
                difficulty_level='beginner',
                subject=row['subject']
            )
            db.session.add(question)
        db.session.commit()
    print('✅ Real questions imported successfully!') 