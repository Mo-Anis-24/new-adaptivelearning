let quizTimer;
let startTime;
let currentQuestion = 0;

const quizId = window.quizId || (window.quiz_data && window.quiz_data.quiz_id) || Date.now();
const localStorageKey = `quiz_answers_${quizId}`;
let answers = {};

function restoreAnswers() {
    const savedAnswers = JSON.parse(localStorage.getItem(localStorageKey) || '{}');
    answers = savedAnswers;
    Object.entries(savedAnswers).forEach(([questionName, answer]) => {
        const radio = document.querySelector(`input[name="${questionName}"][value="${answer}"]`);
        if (radio) {
            radio.checked = true;
            const questionCard = radio.closest('.card');
            if (questionCard) {
                questionCard.classList.add('answered');
                questionCard.style.borderLeftColor = '#198754';
            }
        }
    });
}

function saveAnswer(questionName, value) {
    answers[questionName] = value;
    localStorage.setItem(localStorageKey, JSON.stringify(answers));
}

function setupAnswerListeners() {
    document.querySelectorAll('input[type="radio"]').forEach(radio => {
        radio.addEventListener('change', function () {
            saveAnswer(this.name, this.value);
            const questionCard = this.closest('.card');
            if (questionCard) {
                questionCard.classList.add('answered');
                questionCard.style.borderLeftColor = '#198754';
            }
            updateProgress();
        });
    });
}

function setupClearOnSubmit() {
    const form = document.getElementById('quizForm');
    if (form) {
        form.addEventListener('submit', function () {
            localStorage.removeItem(localStorageKey);
        });
    }
}

function startTimer() {
    const timerElement = document.getElementById('timer');
    if (!timerElement) return;

    quizTimer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

        if (elapsed > 600) {
            timerElement.style.color = '#dc3545';
        } else if (elapsed > 300) {
            timerElement.style.color = '#ffc107';
        } else {
            timerElement.style.color = '#0d6efd';
        }
    }, 1000);
}

function setupQuestionHighlighting() {
    const questions = document.querySelectorAll('.card');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                questions.forEach(q => q.classList.remove('current-question'));
                entry.target.classList.add('current-question');
                currentQuestion = Array.from(questions).indexOf(entry.target);
            }
        });
    }, { threshold: 0.5, rootMargin: '0px 0px -50% 0px' });

    questions.forEach(question => observer.observe(question));
}

function setupFormValidation() {
    const form = document.getElementById('quizForm');
    if (!form) return;

    form.addEventListener('submit', function (e) {
        if (!validateQuiz()) {
            e.preventDefault();
            showValidationMessage();
        } else {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Submitting...';
            }
            clearInterval(quizTimer);

            setTimeout(() => {
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.innerHTML = '<i data-feather="check"></i> Submit Quiz';
                }
            }, 5000);
        }
    });
}

function validateQuiz() {
    const totalQuestions = document.querySelectorAll('.card').length;
    return Object.keys(answers).length === totalQuestions;
}

function showValidationMessage() {
    const unanswered = getUnansweredQuestions();
    const message = `Please answer all questions. You have ${unanswered.length} unanswered question${unanswered.length > 1 ? 's' : ''}.`;

    let alert = document.querySelector('.quiz-validation-alert');
    if (!alert) {
        alert = document.createElement('div');
        alert.className = 'alert alert-warning alert-dismissible fade show quiz-validation-alert';
        alert.innerHTML = `
            <i data-feather="alert-triangle"></i>
            <span class="alert-message">${message}</span>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.container').prepend(alert);
        feather.replace();
    } else {
        alert.querySelector('.alert-message').textContent = message;
    }

    const firstUnanswered = unanswered[0];
    if (firstUnanswered) {
        firstUnanswered.scrollIntoView({ behavior: 'smooth', block: 'center' });
        firstUnanswered.classList.add('highlight-unanswered');
        setTimeout(() => firstUnanswered.classList.remove('highlight-unanswered'), 3000);
    }
}

function getUnansweredQuestions() {
    const questions = document.querySelectorAll('.card');
    return Array.from(questions).filter((_, index) => !answers.hasOwnProperty(`question_${index}`));
}

function updateProgress() {
    const totalQuestions = document.querySelectorAll('.card').length;
    const answeredQuestions = Object.keys(answers).length;
    const progress = (answeredQuestions / totalQuestions) * 100;

    const progressBar = document.querySelector('.quiz-progress');
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
    }

    const submitButton = document.querySelector('button[type="submit"]');
    if (submitButton) {
        if (answeredQuestions === totalQuestions) {
            submitButton.classList.replace('btn-primary', 'btn-success');
            submitButton.innerHTML = '<i data-feather="check"></i> Submit Quiz';
        } else {
            submitButton.classList.replace('btn-success', 'btn-primary');
            submitButton.innerHTML = `<i data-feather="edit"></i> Submit Quiz (${answeredQuestions}/${totalQuestions})`;
        }
        feather.replace();
    }
}

function completeQuiz() {
    if (quizTimer) clearInterval(quizTimer);
    const form = document.getElementById('quizForm');
    if (form && validateQuiz()) form.submit();
}

function showQuizHint(questionIndex) {
    const hint = document.querySelectorAll('.card')[questionIndex]?.querySelector('.quiz-hint');
    if (hint) {
        hint.style.display = 'block';
        hint.classList.add('fade-in');
    }
}

function highlightCorrectAnswer(questionIndex) {
    const correctOption = document.querySelectorAll('.card')[questionIndex]?.querySelector('.correct-answer');
    if (correctOption) correctOption.classList.add('highlight-correct');
}

// DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    startTime = Date.now();
    startTimer();
    restoreAnswers();
    setupAnswerListeners();
    setupClearOnSubmit();
    setupQuestionHighlighting();
    setupQuizNavigation();
    setupFormValidation();

    window.addEventListener('beforeunload', function (e) {
        if (hasUnansweredQuestions()) {
            e.preventDefault();
            e.returnValue = '';
        }
    });
});

function hasUnansweredQuestions() {
    return getUnansweredQuestions().length > 0;
}

function setupQuizNavigation() {
    document.addEventListener('keydown', function (e) {
        if (e.key >= '1' && e.key <= '4') {
            const current = document.querySelector('.card.current-question');
            const options = current?.querySelectorAll('input[type="radio"]');
            const option = options?.[parseInt(e.key) - 1];
            if (option) {
                option.checked = true;
                option.dispatchEvent(new Event('change'));
            }
        }

        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            const submitButton = document.querySelector('button[type="submit"]');
            if (submitButton && !submitButton.disabled) submitButton.click();
        }

        if (e.key === 'Escape') {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    });
}

// Custom styles
const style = document.createElement('style');
style.textContent = `
    .card.answered {
        border-left: 4px solid #198754 !important;
    }
    .card.current-question {
        box-shadow: 0 0 0 2px rgba(13, 110, 253, 0.5);
    }
    .highlight-unanswered {
        animation: pulse 1s infinite;
        border-color: #dc3545 !important;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(220, 53, 69, 0); }
        100% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0); }
    }
    .quiz-progress {
        transition: width 0.3s ease;
    }
    .form-check-input:checked + .form-check-label {
        color: #198754;
        font-weight: 500;
    }
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
`;
document.head.appendChild(style);

