from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    learning_style = db.Column(db.String(50), default='visual')
    skill_level = db.Column(db.String(50), default='beginner')
    phone = db.Column(db.String(20), nullable=True)
    college = db.Column(db.String(120), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    quiz_attempts = db.relationship('QuizAttempt', backref='user', lazy=True)
    interactions = db.relationship('UserInteraction', backref='user', lazy=True)
    predictions = db.relationship('UserPrediction', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_average_score(self):
        if not self.quiz_attempts:
            return 0
        return sum(attempt.score for attempt in self.quiz_attempts) / len(self.quiz_attempts)
    
    def get_total_attempts(self):
        return len(self.quiz_attempts)

class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # 'article', 'video', 'exercise'
    difficulty_level = db.Column(db.String(50), nullable=False)  # 'beginner', 'intermediate', 'advanced'
    subject = db.Column(db.String(100), nullable=False)
    tags = db.Column(db.Text)  # JSON string of tags
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    quiz_questions = db.relationship('QuizQuestion', backref='content', lazy=True)

class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_id = db.Column(db.Integer, db.ForeignKey('content.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text, nullable=False)  # JSON string of options
    correct_answer = db.Column(db.String(10), nullable=False)
    difficulty_level = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    questions = db.Column(db.Text, nullable=False)  # JSON string of question IDs
    answers = db.Column(db.Text, nullable=False)  # JSON string of user answers
    score = db.Column(db.Float, nullable=False)
    time_spent = db.Column(db.Integer, nullable=False)  # in seconds
    difficulty_level = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserInteraction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    interaction_type = db.Column(db.String(50), nullable=False)  # 'quiz', 'content_view', 'click'
    content_id = db.Column(db.Integer, db.ForeignKey('content.id'), nullable=True)
    duration = db.Column(db.Integer, nullable=True)  # in seconds
    interaction_metadata = db.Column(db.Text)  # JSON string for additional data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserPrediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    model_type = db.Column(db.String(50), nullable=False)  # 'random_forest', 'xgboost', 'neural_network'
    predicted_score = db.Column(db.Float, nullable=False)
    actual_score = db.Column(db.Float, nullable=True)
    difficulty_level = db.Column(db.String(50), nullable=False)
    accuracy = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LoginActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(256), nullable=True)
