from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import time
import pandas as pd
import os
import csv
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app import app, db
from models import User, Content, QuizAttempt, UserInteraction, QuizQuestion, PasswordReset
from ml_models import model_manager
from quiz_generator import quiz_generator
from content_manager import get_content_manager
from certificate_generator import CertificateGenerator
import email_config

def send_reset_email(user_email, reset_url):
    """Send password reset email"""
    try:
        # For development, we'll use a simple print instead of actual email
        print(f"Password reset email would be sent to: {user_email}")
        print(f"Reset URL: {reset_url}")
        print("In production, configure SMTP settings to send actual emails")
        
        # Check if Gmail is enabled in email_config.py
        if hasattr(email_config, 'GMAIL_ENABLED') and email_config.GMAIL_ENABLED:
            try:
                msg = MIMEMultipart()
                msg['From'] = email_config.GMAIL_EMAIL
                msg['To'] = user_email
                msg['Subject'] = "Password Reset Request - BroderAI Learning Platform"
                
                body = f"Hello,\n\nYou have requested a password reset for your BroderAI Learning Platform account.\n\nClick the following link to reset your password:\n{reset_url}\n\nThis link will expire in 1 hour.\n\nIf you didn't request this reset, please ignore this email.\n\nBest regards,\nBroderAI Team"
                
                msg.attach(MIMEText(body, 'plain'))
                
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(email_config.GMAIL_EMAIL, email_config.GMAIL_PASSWORD)
                text = msg.as_string()
                server.sendmail(email_config.GMAIL_EMAIL, user_email, text)
                server.quit()
                
                print(f"✅ Email sent successfully to {user_email}")
                return True
                
            except Exception as e:
                print(f"❌ Error sending email via Gmail: {e}")
                print("📧 Email configuration failed. Check email_config.py settings.")
                return False
        else:
            print("📧 Gmail not enabled. Update email_config.py to enable email sending.")
            print("📧 For now, check the console above for the reset link.")
            return True
        
    except Exception as e:
        print(f"Error in send_reset_email: {e}")
        return False

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
    """User login with username or email"""
    if request.method == 'POST':
        username_or_email = request.form['username']
        password = request.form['password']
        
        # Try to find user by username first, then by email
        user = User.query.filter_by(username=username_or_email).first()
        if not user:
            user = User.query.filter_by(email=username_or_email).first()
        
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
            flash('Invalid username/email or password', 'error')
    
    return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password functionality"""
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            # Create password reset record
            reset_record = PasswordReset(
                user_id=user.id,
                token=token,
                expires_at=expires_at
            )
            db.session.add(reset_record)
            db.session.commit()
            
            # Generate reset URL
            reset_url = url_for('reset_password', token=token, _external=True)
            
            # Send reset email
            if send_reset_email(email, reset_url):
                flash('Password reset link has been sent to your email address.', 'success')
            else:
                flash('Error sending reset email. Please try again later.', 'error')
        else:
            # Don't reveal if email exists or not for security
            flash('If an account with that email exists, a password reset link has been sent.', 'success')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    # Find the reset record
    reset_record = PasswordReset.query.filter_by(
        token=token, 
        used=False
    ).first()
    
    if not reset_record:
        flash('Invalid or expired reset link.', 'error')
        return redirect(url_for('login'))
    
    if reset_record.expires_at < datetime.utcnow():
        flash('Reset link has expired. Please request a new one.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('reset_password.html', token=token)
        
        # Update user password
        user = User.query.get(reset_record.user_id)
        user.set_password(password)
        
        # Mark reset token as used
        reset_record.used = True
        
        db.session.commit()
        
        flash('Your password has been reset successfully. You can now login with your new password.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

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

# Certificate verification route using database
@app.route('/vb', methods=['GET', 'POST'])
def verify_search():
    cert_data = None
    error = None
    if request.method == 'POST':
        series_id = request.form.get('series_id', '').strip()
        if not series_id.isdigit():
            error = 'Please enter a valid numeric Series ID.'
        else:
            try:
                cert_gen = CertificateGenerator()
                verification_result = cert_gen.verify_certificate(series_id)
                
                if verification_result.get('valid'):
                    cert_data = verification_result
                else:
                    error = verification_result.get('message', 'Certificate not found for this Series ID.')
            except Exception as e:
                error = f'Error verifying certificate: {str(e)}'
    return render_template('verify_search.html', cert_data=cert_data, error=error)
    
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
