from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import time
import pandas as pd
import os
import csv

from app import app, db
from models import User, Content, QuizAttempt, UserInteraction, QuizQuestion
from ml_models import model_manager
from quiz_generator import quiz_generator
from content_manager import get_content_manager
from certificate_generator import CertificateGenerator

@app.route('/')
def index():
    """Homepage"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        learning_style = request.form.get('learning_style', 'visual')
        skill_level = request.form.get('skill_level', 'beginner')
        phone = request.form['phone']
        college = request.form['college']
        age = request.form['age']
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            learning_style=learning_style,
            skill_level=skill_level,
            phone=phone,
            college=college,
            age=age
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            # Log login activity
            from models import LoginActivity
            login_activity = LoginActivity(
                user_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(login_activity)
            db.session.commit()
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with ML predictions and analytics"""
    # Train models if not already trained
    if not model_manager.random_forest_model:
        model_manager.train_all_models()
    
    # Get predictions from all models
    predictions = model_manager.predict_score(current_user)
    
    # Get quiz statistics
    quiz_stats = quiz_generator.get_quiz_statistics(current_user)
    
    # Get recommended content
    content_mgr = get_content_manager()
    recommended_content = content_mgr.get_recommended_content(current_user, predictions)
    
    # Get recent quiz attempts
    recent_attempts = QuizAttempt.query.filter_by(
        user_id=current_user.id
    ).order_by(QuizAttempt.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html',
                         predictions=predictions,
                         quiz_stats=quiz_stats,
                         recommended_content=recommended_content,
                         recent_attempts=recent_attempts)

@app.route('/start_quiz', methods=['GET', 'POST'])
@login_required
def start_quiz():
    """Show subject selection form and handle submission"""
    if request.method == 'POST':
        subject = request.form['subject']
        return redirect(url_for('quiz', subject=subject))
    # Get all unique subjects from QuizQuestion (including new ones)
    subjects = db.session.query(QuizQuestion.subject).distinct().all()
    subjects = [s[0] for s in subjects]
    return render_template('start_quiz.html', subjects=subjects)

@app.route('/quiz')
@login_required
def quiz():
    """Generate and display adaptive quiz"""
    # Get predictions for quiz generation
    predictions = model_manager.predict_score(current_user)
    subject = request.args.get('subject')
    if not subject:
        flash('Please select a subject to start the quiz.', 'error')
        return redirect(url_for('start_quiz'))
    # Generate adaptive quiz
    quiz_data = quiz_generator.generate_adaptive_quiz(current_user, predictions, subject)
    # Store quiz data in session
    session['current_quiz'] = quiz_data
    session['quiz_start_time'] = time.time()
    return render_template('quiz.html', quiz_data=quiz_data)

@app.route('/submit_quiz', methods=['POST'])
@login_required
def submit_quiz():
    """Submit quiz answers and get results"""
    if 'current_quiz' not in session:
        flash('No active quiz found', 'error')
        return redirect(url_for('dashboard'))
    
    quiz_data = session['current_quiz']
    start_time = session.get('quiz_start_time', time.time())
    time_spent = int(time.time() - start_time)
    
    # Get user answers
    user_answers = []
    for i in range(len(quiz_data['questions'])):
        answer = request.form.get(f'question_{i}')
        user_answers.append(answer)
    
    # Evaluate quiz
    results = quiz_generator.evaluate_quiz(current_user, quiz_data, user_answers, time_spent)

    results['subject'] = quiz_data['subject']
    results['score'] = results['score']
    
    # Update prediction accuracy
    model_manager.update_prediction_accuracy(current_user.id, results['score'])
    
    # Create enhanced dataset for better predictions
    model_manager.create_enhanced_user_dataset(current_user, quiz_data, user_answers, results)
    
    # --- Append to CSV and retrain model ---
    new_row = {
        'user_id': current_user.id,
        'subject': quiz_data['subject'],
        'difficulty': quiz_data['difficulty_level'],
        'score': results['score'],
        'time_spent': results['time_spent'],
        'learning_style': current_user.learning_style,
        'skill_level': current_user.skill_level
    }
    csv_path = 'student_quiz_data.csv'
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(csv_path, index=False)
    else:
        pd.DataFrame([new_row]).to_csv(csv_path, index=False)
    # Retrain model on updated CSV
    model_manager.train_from_csv(csv_path)
    # --- End CSV/model update ---
    
    # Generate updated predictions based on new data (for next quiz)
    next_predictions = model_manager.predict_score(current_user)
    results['next_predictions'] = next_predictions
    
    # Clear session
    session.pop('current_quiz', None)
    session.pop('quiz_start_time', None)
    
    return render_template('results.html', results=results)

@app.route('/content')
@login_required
def content():
    """Display available content"""
    difficulty_filter = request.args.get('difficulty', 'all')
    
    content_mgr = get_content_manager()
    
    if difficulty_filter == 'all':
        content_list = content_mgr.get_all_content()
    else:
        content_list = content_mgr.get_content_by_difficulty(difficulty_filter)
    
    return render_template('content.html', 
                         content_list=content_list,
                         current_filter=difficulty_filter)

@app.route('/content/<int:content_id>')
@login_required
def view_content(content_id):
    """View specific content"""
    content_item = Content.query.get_or_404(content_id)
    
    # Record user interaction
    interaction = UserInteraction(
        user_id=current_user.id,
        interaction_type='content_view',
        content_id=content_id,
        duration=0,  # Will be updated via JavaScript
        interaction_metadata=json.dumps({'content_type': content_item.content_type})
    )
    db.session.add(interaction)
    db.session.commit()
    
    return render_template('content_detail.html', content=content_item)

@app.route('/api/model_predictions')
@login_required
def api_model_predictions():
    """API endpoint for real-time model predictions"""
    predictions = model_manager.predict_score(current_user)
    return jsonify(predictions)

@app.route('/api/quiz_stats')
@login_required
def api_quiz_stats():
    """API endpoint for quiz statistics"""
    stats = quiz_generator.get_quiz_statistics(current_user)
    return jsonify(stats)

@app.route('/api/retrain_models', methods=['POST'])
@login_required
def api_retrain_models():
    """API endpoint to retrain ML models"""
    try:
        success = model_manager.train_all_models()
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download_certificate')
@login_required
def download_certificate():
    """Generate and send certificate PDF if score >= 70%"""
    subject = request.args.get('subject')
    score = request.args.get('score', type=float)
    if not subject or score is None:
        flash('Invalid certificate request', 'error')
        return redirect(url_for('dashboard'))
    if score < 70:
        flash('Certificate is only available for scores 70% and above.', 'error')
        return redirect(url_for('dashboard'))
    user_name = current_user.username
    date_str = datetime.now().strftime('%d %b %Y')
    cert_gen = CertificateGenerator()
    pdf_bytes = cert_gen.generate_certificate(user_name, subject, int(score), date_str)
    return app.response_class(
        pdf_bytes,
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename=certificate_{subject}_{user_name}.pdf'
        }
    )

# Remove the old verify_certificate route
# Add new public verification route
@app.route('/vb', methods=['GET', 'POST'])
def verify_search():
    cert_data = None
    error = None
    if request.method == 'POST':
        series_id = request.form.get('series_id', '').strip()
        if not series_id.isdigit():
            error = 'Please enter a valid numeric Series ID.'
        else:
            cert_file = 'certificates.csv'
            try:
                import csv
                with open(cert_file, newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        if row['series_id'] == series_id:
                            cert_data = row
                            break
                    if not cert_data:
                        error = 'Certificate not found for this Series ID.'
            except FileNotFoundError:
                error = 'No certificates have been issued yet.'
    return render_template('verify_search.html', cert_data=cert_data, error=error)
    
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
