import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
import xgboost as xgb
import joblib
import logging
import json
from datetime import datetime, timedelta
from models import User, QuizAttempt, UserInteraction, UserPrediction
from app import db
import os

class MLModelManager:
    def __init__(self):
        self.random_forest_model = None
        self.xgboost_model = None
        self.neural_network_model = None
        self.scaler = StandardScaler()
        self.feature_columns = [
            'avg_score', 'total_attempts', 'time_spent_avg', 'days_since_last_attempt',
            'difficulty_progression', 'interaction_frequency', 'learning_style_encoded'
        ]
        
    def prepare_features(self, user_data):
        """Prepare enhanced features for ML models"""
        features = []
        
        for user in user_data:
            # Calculate basic statistics
            avg_score = user.get_average_score()
            total_attempts = user.get_total_attempts()
            
            # Calculate time-based features
            time_spent_avg = 0
            days_since_last_attempt = 30  # default
            
            if user.quiz_attempts:
                time_spent_avg = np.mean([attempt.time_spent for attempt in user.quiz_attempts])
                last_attempt = max(user.quiz_attempts, key=lambda x: x.created_at)
                days_since_last_attempt = (datetime.utcnow() - last_attempt.created_at).days
            
            # Calculate difficulty progression
            difficulty_progression = 0
            if len(user.quiz_attempts) >= 2:
                difficulty_levels = {'beginner': 1, 'intermediate': 2, 'advanced': 3}
                recent_attempts = sorted(user.quiz_attempts, key=lambda x: x.created_at)[-5:]
                if len(recent_attempts) >= 2:
                    difficulty_progression = (
                        difficulty_levels.get(recent_attempts[-1].difficulty_level, 1) - 
                        difficulty_levels.get(recent_attempts[0].difficulty_level, 1)
                    )
            
            # Calculate interaction frequency
            interaction_frequency = len(user.interactions) / max(1, days_since_last_attempt)
            
            # Enhanced features from quiz performance
            subject_consistency = 0
            prediction_accuracy = 0
            
            # Get enhanced interactions for better features
            enhanced_interactions = UserInteraction.query.filter_by(
                user_id=user.id,
                interaction_type='enhanced_quiz'
            ).all()
            
            if enhanced_interactions:
                subject_scores = []
                accuracy_scores = []
                
                for interaction in enhanced_interactions:
                    try:
                        import json
                        metadata = json.loads(interaction.interaction_metadata)
                        
                        # Subject consistency
                        if 'subject_performance' in metadata:
                            subject_perf = metadata['subject_performance']
                            for subject, perf in subject_perf.items():
                                if perf['total'] > 0:
                                    subject_scores.append(perf['correct'] / perf['total'])
                        
                        # Prediction accuracy
                        if 'actual_vs_predicted' in metadata:
                            pred_errors = metadata['actual_vs_predicted']
                            avg_error = sum(pred_errors.values()) / len(pred_errors) if pred_errors else 0
                            accuracy_scores.append(max(0, 100 - avg_error))
                            
                    except (json.JSONDecodeError, KeyError):
                        continue
                
                subject_consistency = sum(subject_scores) / len(subject_scores) if subject_scores else 0
                prediction_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0
            
            # Encode learning style
            learning_style_encoded = {
                'visual': 1, 'auditory': 2, 'kinesthetic': 3, 'reading': 4
            }.get(user.learning_style, 1)
            
            features.append([
                avg_score, total_attempts, time_spent_avg, days_since_last_attempt,
                difficulty_progression, interaction_frequency, learning_style_encoded,
                subject_consistency, prediction_accuracy
            ])
        
        return np.array(features)
    
    def prepare_target(self, user_data):
        """Prepare target variable (next quiz score)"""
        targets = []
        for user in user_data:
            # Use the most recent score as target, or average if available
            if user.quiz_attempts:
                recent_score = user.quiz_attempts[-1].score
                targets.append(recent_score)
            else:
                targets.append(50.0)  # default score for new users
        return np.array(targets)
    
    def train_random_forest(self, X, y):
        """Train Random Forest model"""
        self.random_forest_model = RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            max_depth=10,
            min_samples_split=5
        )
        self.random_forest_model.fit(X, y)
        logging.info("Random Forest model trained successfully")
    
    def train_xgboost(self, X, y):
        """Train XGBoost model"""
        self.xgboost_model = xgb.XGBRegressor(
            n_estimators=100,
            random_state=42,
            max_depth=6,
            learning_rate=0.1
        )
        self.xgboost_model.fit(X, y)
        logging.info("XGBoost model trained successfully")
    
    def train_neural_network(self, X, y):
        """Train Neural Network model using sklearn MLPRegressor"""
        self.neural_network_model = MLPRegressor(
            hidden_layer_sizes=(64, 32, 16),
            max_iter=500,
            random_state=42,
            alpha=0.001,
            learning_rate_init=0.001
        )
        self.neural_network_model.fit(X, y)
        logging.info("Neural Network model trained successfully")
    
    def train_all_models(self):
        """Train all ML models with current user data"""
        # Get user data
        users = User.query.all()
        
        if len(users) < 10:  # Need minimum data for training
            logging.warning("Not enough user data for training models")
            return False
        
        # Prepare features and targets
        X = self.prepare_features(users)
        y = self.prepare_target(users)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train models
        self.train_random_forest(X_scaled, y)
        self.train_xgboost(X_scaled, y)
        self.train_neural_network(X_scaled, y)
        
        return True
    
    def train_from_csv(self, csv_path='student_quiz_data.csv'):
        """Train models using synthetic student quiz data from CSV."""
        if not os.path.exists(csv_path):
            print(f"CSV file {csv_path} not found.")
            return False
        df = pd.read_csv(csv_path)
        # Encode categorical variables
        df['subject'] = df['subject'].astype('category').cat.codes
        df['difficulty'] = df['difficulty'].astype('category').cat.codes
        df['learning_style'] = df['learning_style'].astype('category').cat.codes
        df['skill_level'] = df['skill_level'].astype('category').cat.codes
        X = df[['subject', 'difficulty', 'time_spent', 'learning_style', 'skill_level']]
        y = df['score']
        X_scaled = self.scaler.fit_transform(X)
        self.train_random_forest(X_scaled, y)
        self.train_xgboost(X_scaled, y)
        self.train_neural_network(X_scaled, y)
        print("Models trained on synthetic student_quiz_data.csv!")
        return True

    def get_default_predictions(self, user, difficulty_level='intermediate'):
        """Get default predictions when models aren't trained"""
        # Base prediction on user's skill level and past performance
        avg_score = user.get_average_score()
        
        if avg_score is None:
            # New user - predict based on skill level
            skill_scores = {
                'beginner': 45.0,
                'intermediate': 60.0,
                'advanced': 75.0
            }
            base_score = skill_scores.get(user.skill_level, 50.0)
        else:
            base_score = avg_score
        
        # Adjust based on difficulty level
        difficulty_adjustments = {
            'beginner': 10.0,
            'intermediate': 0.0,
            'advanced': -10.0
        }
        
        adjusted_score = base_score + difficulty_adjustments.get(difficulty_level, 0.0)
        adjusted_score = max(0, min(100, adjusted_score))
        
        # Return similar predictions for all models with slight variations
        predictions = {
            'random_forest': max(0, min(100, adjusted_score + 2)),
            'xgboost': max(0, min(100, adjusted_score - 1)),
            'neural_network': max(0, min(100, adjusted_score + 1))
        }
        
        return predictions
    
    def create_enhanced_user_dataset(self, user, quiz_data, user_answers, results):
        """Create enhanced dataset entry based on quiz performance"""
        try:
            # Analyze user performance patterns
            correct_answers = 0
            subject_performance = {}
            difficulty_performance = {}
            
            for i, question in enumerate(quiz_data['questions']):
                user_answer = user_answers[i] if i < len(user_answers) else None
                is_correct = user_answer == question['correct_answer']
                
                if is_correct:
                    correct_answers += 1
                
                # Track subject performance
                subject = question['subject']
                if subject not in subject_performance:
                    subject_performance[subject] = {'correct': 0, 'total': 0}
                subject_performance[subject]['total'] += 1
                if is_correct:
                    subject_performance[subject]['correct'] += 1
                
                # Track difficulty performance
                difficulty = question['difficulty_level']
                if difficulty not in difficulty_performance:
                    difficulty_performance[difficulty] = {'correct': 0, 'total': 0}
                difficulty_performance[difficulty]['total'] += 1
                if is_correct:
                    difficulty_performance[difficulty]['correct'] += 1
            
            # Create detailed interaction record
            interaction_metadata = {
                'quiz_score': results['score'],
                'time_spent': results['time_spent'],
                'correct_answers': correct_answers,
                'total_questions': len(quiz_data['questions']),
                'subject_performance': subject_performance,
                'difficulty_performance': difficulty_performance,
                'learning_style': user.skill_level,
                'predicted_scores': quiz_data.get('predictions', {}),
                'actual_vs_predicted': {
                    model: abs(results['score'] - pred) 
                    for model, pred in quiz_data.get('predictions', {}).items()
                }
            }
            
            # Store enhanced interaction
            from models import UserInteraction
            interaction = UserInteraction(
                user_id=user.id,
                interaction_type='enhanced_quiz',
                duration=results['time_spent'],
                interaction_metadata=json.dumps(interaction_metadata)
            )
            db.session.add(interaction)
            db.session.commit()
            
            logging.info(f"Enhanced dataset created for user {user.id}")
            
        except Exception as e:
            logging.error(f"Error creating enhanced dataset: {str(e)}")
    
    def predict_score(self, user, difficulty_level='intermediate'):
        """Predict score for a user using all models"""
        try:
            # Check if scaler is fitted
            if not hasattr(self.scaler, 'scale_'):
                return self.get_default_predictions(user, difficulty_level)
            
            # Prepare user features
            user_features = self.prepare_features([user])
            user_features_scaled = self.scaler.transform(user_features)
            
            predictions = {}
            
            # Random Forest prediction
            if self.random_forest_model:
                rf_pred = self.random_forest_model.predict(user_features_scaled)[0]
                predictions['random_forest'] = max(0, min(100, rf_pred))
            
            # XGBoost prediction
            if self.xgboost_model:
                xgb_pred = self.xgboost_model.predict(user_features_scaled)[0]
                predictions['xgboost'] = max(0, min(100, xgb_pred))
            
            # Neural Network prediction
            if self.neural_network_model:
                nn_pred = self.neural_network_model.predict(user_features_scaled)[0]
                predictions['neural_network'] = max(0, min(100, nn_pred))
            
            # If no predictions were made, return defaults
            if not predictions:
                return self.get_default_predictions(user, difficulty_level)
            
            # Store predictions in database
            for model_type, pred_score in predictions.items():
                prediction = UserPrediction(
                    user_id=user.id,
                    model_type=model_type,
                    predicted_score=pred_score,
                    difficulty_level=difficulty_level
                )
                db.session.add(prediction)
            
            db.session.commit()
            
            return predictions
            
        except Exception as e:
            logging.error(f"Error in predict_score: {str(e)}")
            return self.get_default_predictions(user, difficulty_level)
    
    def get_ensemble_prediction(self, user, difficulty_level='intermediate'):
        """Get ensemble prediction from all models"""
        predictions = self.predict_score(user, difficulty_level)
        
        if not predictions:
            return 50.0  # default score
        
        # Calculate weighted average (can be adjusted based on model performance)
        weights = {'random_forest': 0.3, 'xgboost': 0.4, 'neural_network': 0.3}
        
        ensemble_score = sum(predictions.get(model, 50.0) * weight 
                           for model, weight in weights.items())
        
        return ensemble_score
    
    def update_prediction_accuracy(self, user_id, actual_score):
        """Update prediction accuracy after quiz completion"""
        recent_predictions = UserPrediction.query.filter_by(
            user_id=user_id,
            actual_score=None
        ).order_by(UserPrediction.created_at.desc()).limit(3).all()
        
        for prediction in recent_predictions:
            accuracy = 100 - abs(prediction.predicted_score - actual_score)
            prediction.actual_score = actual_score
            prediction.accuracy = max(0, accuracy)
        
        db.session.commit()

# Initialize the global model manager
model_manager = MLModelManager()

if __name__ == "__main__":
    model_manager = MLModelManager()
    model_manager.train_from_csv()
