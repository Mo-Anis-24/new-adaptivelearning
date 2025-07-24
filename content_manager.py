import json
from models import Content, QuizQuestion
from app import db

class ContentManager:
    def __init__(self):
        pass
    # Remove initialize_content logic that seeds sample questions
    def get_recommended_content(self, user, predictions):
        ensemble_score = sum(predictions.values()) / len(predictions) if predictions else 50.0
        if ensemble_score < 40:
            target_difficulty = 'beginner'
        elif ensemble_score < 70:
            target_difficulty = 'intermediate'
        else:
            target_difficulty = 'advanced'
        recommended_content = Content.query.filter_by(
            difficulty_level=target_difficulty
        ).all()
        return recommended_content
    def get_content_by_difficulty(self, difficulty_level):
        return Content.query.filter_by(difficulty_level=difficulty_level).all()
    def get_all_content(self):
        return Content.query.all()
content_manager = None
def get_content_manager():
    global content_manager
    if content_manager is None:
        content_manager = ContentManager()
    return content_manager
