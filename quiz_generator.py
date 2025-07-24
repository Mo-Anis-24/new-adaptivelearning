import json
import random
from models import QuizQuestion, QuizAttempt, UserInteraction
from app import db

class QuizGenerator:
    def __init__(self):
        pass

    def generate_adaptive_quiz(self, user, predictions, subject, num_questions=15):
        """Generate a quiz with 15 random questions from the selected subject."""
        all_questions = QuizQuestion.query.filter_by(subject=subject).all()
        if len(all_questions) <= num_questions:
            questions = all_questions
        else:
            questions = random.sample(all_questions, num_questions)
        quiz_data = {
            'difficulty_level': 'beginner',
            'questions': [],
            'predictions': predictions,
            'subject': subject
        }
        for question in questions:
            quiz_data['questions'].append({
                'id': question.id,
                'question_text': question.question_text,
                'options': json.loads(question.options),
                'correct_answer': question.correct_answer,
                'difficulty_level': question.difficulty_level,
                'subject': question.subject
            })
        return quiz_data

    def evaluate_quiz(self, user, quiz_data, user_answers, time_spent):
        """Evaluate quiz and store results"""
        total_questions = len(quiz_data['questions'])
        correct_answers = 0

        for i, question in enumerate(quiz_data['questions']):
            if i < len(user_answers) and user_answers[i] == question['correct_answer']:
                correct_answers += 1

        score = (correct_answers / total_questions) * 100

        # Create quiz attempt record
        quiz_attempt = QuizAttempt(
            user_id=user.id,
            questions=json.dumps([q['id'] for q in quiz_data['questions']]),
            answers=json.dumps(user_answers),
            score=score,
            time_spent=time_spent,
            difficulty_level=quiz_data['difficulty_level']
        )

        db.session.add(quiz_attempt)

        # Create user interaction record
        interaction = UserInteraction(
            user_id=user.id,
            interaction_type='quiz',
            duration=time_spent,
            interaction_metadata=json.dumps({
                'score': score,
                'difficulty': quiz_data['difficulty_level'],
                'correct_answers': correct_answers,
                'total_questions': total_questions
            })
        )

        db.session.add(interaction)
        db.session.commit()

        # Calculate detailed results
        results = {
            'score': score,
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'time_spent': time_spent,
            'difficulty_level': quiz_data['difficulty_level'],
            'predictions': quiz_data.get('predictions', {}),
            'questions_review': []
        }

        for i, question in enumerate(quiz_data['questions']):
            user_answer = user_answers[i] if i < len(user_answers) else None
            results['questions_review'].append({
                'question_text': question['question_text'],
                'options': question['options'],
                'correct_answer': question['correct_answer'],
                'user_answer': user_answer,
                'is_correct': user_answer == question['correct_answer'],
                'subject': question['subject']
            })

        return results

    def get_difficulty_recommendation(self, user, current_score):
        """Recommend next difficulty level based on performance"""
        user_avg = user.get_average_score()

        if current_score >= 80 and user_avg >= 75:
            return 'advanced'
        elif current_score >= 60 and user_avg >= 55:
            return 'intermediate'
        else:
            return 'beginner'

    def get_quiz_statistics(self, user):
        """Get user's quiz statistics"""
        attempts = QuizAttempt.query.filter_by(user_id=user.id).all()

        if not attempts:
            return {
                'total_attempts': 0,
                'average_score': 0,
                'best_score': 0,
                'difficulty_breakdown': {},
                'subject_performance': {},
                'recent_scores': []
            }

        scores = [attempt.score for attempt in attempts]
        difficulty_breakdown = {}
        subject_performance = {}

        for attempt in attempts:
            # Difficulty breakdown
            diff = attempt.difficulty_level
            if diff not in difficulty_breakdown:
                difficulty_breakdown[diff] = {'count': 0, 'avg_score': 0}
            difficulty_breakdown[diff]['count'] += 1
            difficulty_breakdown[diff]['avg_score'] = (
                difficulty_breakdown[diff]['avg_score'] + attempt.score
            ) / difficulty_breakdown[diff]['count']

            # Subject performance (from questions)
            questions = json.loads(attempt.questions)
            for question_id in questions:
                question = QuizQuestion.query.get(question_id)
                if question:
                    subject = question.subject
                    if subject not in subject_performance:
                        subject_performance[subject] = {'count': 0, 'avg_score': 0}
                    subject_performance[subject]['count'] += 1
                    subject_performance[subject]['avg_score'] = (
                        subject_performance[subject]['avg_score'] + attempt.score
                    ) / subject_performance[subject]['count']

        return {
            'total_attempts': len(attempts),
            'average_score': sum(scores) / len(scores),
            'best_score': max(scores),
            'difficulty_breakdown': difficulty_breakdown,
            'subject_performance': subject_performance,
            'recent_scores': scores[-10:]  # Last 10 scores
        }

# Initialize the global quiz generator
quiz_generator = QuizGenerator()
