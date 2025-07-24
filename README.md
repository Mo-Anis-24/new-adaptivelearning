# Adaptive Learning Platform

## Overview

This is a Flask-based adaptive learning platform that uses machine learning to personalize educational content and quizzes. The system employs multiple ML models (Random Forest, XGBoost, Neural Networks) to predict student performance and adapt content difficulty accordingly. The platform provides intelligent quiz generation, real-time performance tracking, and comprehensive analytics.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

### July 16, 2025 - Enhanced Quiz Submission and Dataset Creation
- **Fixed quiz submit button**: Resolved validation issues so quiz submission works properly
- **Implemented enhanced dataset creation**: Quiz responses now create detailed datasets with subject performance, difficulty analysis, and prediction accuracy tracking
- **Enhanced ML model features**: Added new features including subject consistency, prediction accuracy, and difficulty progression to improve score predictions
- **Added updated predictions display**: After quiz completion, users see updated predictions for their next quiz based on their performance
- **Improved results page**: Added sections showing prediction accuracy and updated score predictions for better user feedback
- **Enhanced error handling**: Added proper JSON imports and fixed template structure issues

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap for responsive UI
- **Styling**: Bootstrap 5 with custom CSS for dark theme
- **JavaScript**: Vanilla JavaScript with Chart.js for data visualization
- **Interactive Elements**: Real-time quiz timer, progress charts, and adaptive navigation

### Backend Architecture
- **Framework**: Flask with Flask-SQLAlchemy for database operations
- **Authentication**: Flask-Login for session management
- **ML Framework**: scikit-learn, XGBoost, and TensorFlow for predictive modeling
- **Architecture Pattern**: Model-View-Controller (MVC) structure

### Data Storage
- **Database**: SQLite for development with PostgreSQL support via SQLAlchemy
- **ORM**: SQLAlchemy with declarative base for database models
- **Session Management**: Flask session handling with configurable secret keys

## Key Components

### Authentication System
- User registration and login with password hashing
- Session-based authentication using Flask-Login
- Learning style and skill level profiling during registration

### Machine Learning Engine (`ml_models.py`)
- **MLModelManager**: Coordinates multiple ML models for performance prediction
- **Models Used**: Random Forest, XGBoost, Neural Networks
- **Feature Engineering**: Calculates user metrics like average scores, time spent, difficulty progression
- **Ensemble Predictions**: Combines predictions from multiple models for better accuracy

### Content Management (`content_manager.py`)
- **ContentManager**: Handles educational content initialization and management
- **Content Types**: Articles, videos, and exercises with difficulty levels
- **Tagging System**: JSON-based tagging for content categorization

### Quiz System (`quiz_generator.py`)
- **QuizGenerator**: Creates adaptive quizzes based on ML predictions
- **Difficulty Adaptation**: Adjusts question difficulty based on predicted performance
- **Question Selection**: Intelligent question sampling based on user proficiency

### Database Models (`models.py`)
- **User**: Stores user profiles, learning preferences, and authentication data
- **Content**: Educational content with metadata and difficulty levels
- **QuizAttempt**: Quiz results and performance tracking
- **UserInteraction**: User engagement metrics and learning analytics

## Data Flow

1. **User Registration**: Captures learning style and skill level preferences
2. **ML Feature Extraction**: Analyzes user performance history and interaction patterns
3. **Prediction Generation**: Multiple ML models predict user performance
4. **Content Adaptation**: Quiz difficulty and content recommendations based on predictions
5. **Performance Tracking**: Results stored and used to retrain models
6. **Analytics Dashboard**: Real-time visualization of learning progress

## External Dependencies

### Core Dependencies
- **Flask**: Web framework for application structure
- **SQLAlchemy**: Database ORM and query builder
- **scikit-learn**: Machine learning algorithms and preprocessing
- **XGBoost**: Gradient boosting framework for predictions
- **scikit-learn MLPRegressor**: Neural network implementation for performance predictions
- **Bootstrap**: Frontend CSS framework for responsive design
- **Chart.js**: JavaScript library for data visualization

### Development Dependencies
- **Werkzeug**: WSGI utilities and development server
- **Jinja2**: Template engine for HTML rendering
- **NumPy/Pandas**: Data manipulation and analysis

## Deployment Strategy

### Environment Configuration
- **Development**: SQLite database with debug mode enabled
- **Production**: PostgreSQL support with environment variable configuration
- **Security**: Session secrets and database URLs configured via environment variables

### Application Structure
- **Entry Point**: `main.py` runs the Flask application
- **App Factory**: `app.py` initializes Flask app and extensions
- **Route Handling**: `routes.py` contains all HTTP endpoints
- **Static Assets**: CSS and JavaScript files served from `/static`

### Database Management
- **Migration Support**: SQLAlchemy handles database schema creation
- **Connection Pooling**: Configured for production with connection recycling
- **Initialization**: Content and quiz data seeded on first run

The application follows a modular architecture with clear separation of concerns, making it easy to extend with additional ML models, content types, or learning analytics features.