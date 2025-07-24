#!/usr/bin/env python3
"""
Test script to verify quiz functionality
"""

from app import app, db
from models import User, QuizQuestion
from quiz_generator import quiz_generator
from ml_models import model_manager

def test_quiz_generation():
    """Test quiz generation and submission"""
    with app.app_context():
        # Get a user
        user = User.query.first()
        if not user:
            print("❌ No users found. Please register a user first.")
            return
        print(f"✅ Testing with user: {user.username}")
        # Get predictions
        predictions = model_manager.predict_score(user)
        print(f"✅ Predictions: {predictions}")
        # Get a subject
        subject = db.session.query(QuizQuestion.subject).first()
        if not subject or not subject[0]:
            print("❌ No subjects found in QuizQuestion table.")
            return
        subject = subject[0]
        print(f"✅ Using subject: {subject}")
        # Generate quiz
        quiz_data = quiz_generator.generate_adaptive_quiz(user, predictions, subject)
        print(f"✅ Quiz generated with {len(quiz_data['questions'])} questions")
        # Print question details
        for i, q in enumerate(quiz_data['questions']):
            print(f"  Question {i+1}: {q['question_text'][:50]}...")
            print(f"    Options: {len(q['options'])} options")
            print(f"    Correct: {q['correct_answer']}")
            print(f"    Difficulty: {q['difficulty_level']}")
            print(f"    Subject: {q['subject']}")
        # Test evaluation with sample answers
        sample_answers = ['A'] * len(quiz_data['questions'])  # All A's
        results = quiz_generator.evaluate_quiz(user, quiz_data, sample_answers, 120)
        print(f"✅ Quiz evaluation completed:")
        print(f"  Score: {results['score']}%")
        print(f"  Correct: {results['correct_answers']}/{results['total_questions']}")
        print(f"  Time spent: {results['time_spent']} seconds")
        print("\n🎉 Quiz functionality test completed successfully!")

if __name__ == "__main__":
    test_quiz_generation() 