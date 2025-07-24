# Adaptive Learning Platform – Change Log & Migration Guide

## Overview

This document summarizes all the changes, fixes, and improvements made to the Adaptive Learning Platform to ensure it runs smoothly, especially on modern Python environments (Python 3.13+), and to fix quiz submission and dynamic question rendering issues.

---

## 1. Environment & Dependency Fixes

### a. Python & Dependency Compatibility
- **Problem:** The project was not compatible with Python 3.13 due to TensorFlow and NumPy version conflicts.
- **Solution:**
  - Updated `requirements.txt` and `pyproject.toml` to:
    - Remove TensorFlow (temporarily, as it does not support Python 3.13).
    - Restrict NumPy to `<2.0.0` for compatibility with other ML libraries.
    - Ensure all other dependencies are compatible with Python 3.13.

### b. XGBoost & OpenMP
- **Problem:** XGBoost could not load due to missing OpenMP runtime (`libomp.dylib`) on macOS.
- **Solution:**
  - Installed OpenMP using Homebrew:
    ```sh
    brew install libomp
    ```
  - This allows XGBoost to function correctly on macOS ARM and Intel.

---

## 2. Quiz System Fixes

### a. Dynamic Question Count
- **Problem:** The quiz page and submission logic were mismatched. The frontend expected 10 questions, but only 5 were generated, causing submission errors.
- **Solution:**
  - Updated the quiz generator to use the actual number of available questions.
  - Made the quiz template dynamically display the correct number of questions using Jinja2:
    ```jinja2
    <div class="questions-count"><i class="fas fa-list-ol"></i> {{ quiz_data.questions|length }} Questions</div>
    ```
  - Updated progress and answer counters to use the real question count.

### b. Frontend Quiz Rendering
- **Problem:** The quiz page used hardcoded sample questions in JavaScript, ignoring the actual quiz data from Flask.
- **Solution:**
  - Passed the real quiz data from Flask to the template:
    ```jinja2
    const quizData = {{ quiz_data.questions|tojson|safe }};
    ```
  - Updated all JavaScript logic to use the real quiz data structure (`question_text`, `options`, etc.).
  - Ensured the quiz renders the correct number of questions and options.

### c. Quiz Submission
- **Problem:** The form did not submit the user's answers correctly, and validation was not dynamic.
- **Solution:**
  - Wrapped the quiz in a `<form>` that posts to `/submit_quiz`.
  - On option selection, created hidden inputs for each answer:
    ```js
    let input = document.querySelector(`input[name="question_${questionIndex}"]`);
    if (!input) {
        input = document.createElement('input');
        input.type = 'hidden';
        input.name = `question_${questionIndex}`;
        document.getElementById('quizForm').appendChild(input);
    }
    input.value = String.fromCharCode(65 + parseInt(optionIndex));
    ```
  - Added client-side validation to prevent submission until all questions are answered.

---

## 3. Database Initialization

### a. Content & Quiz Data
- **Problem:** The database and content were not always initialized, leading to missing questions.
- **Solution:**
  - Added `init_db.py` script to initialize the database and seed sample content/questions.
  - Usage:
    ```sh
    python3 init_db.py
    ```

---

## 4. Testing & Verification

### a. Test Script
- **Problem:** Needed a way to verify quiz generation and evaluation.
- **Solution:**
  - Added `test_quiz.py` to programmatically test quiz generation, answer submission, and scoring.
  - Usage:
    ```sh
    python3 test_quiz.py
    ```

---

## 5. Port & Server Issues

### a. Port Conflicts
- **Problem:** Port 5000 was in use by macOS Control Center.
- **Solution:**
  - Changed the Flask app to run on port 8000 in `main.py`:
    ```python
    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=8000, debug=True)
    ```

---

## 6. Summary of Files Changed

- **requirements.txt**: Updated/remodeled dependencies for Python 3.13 compatibility.
- **pyproject.toml**: Fixed TOML formatting and dependencies.
- **main.py**: Changed default port to 8000.
- **init_db.py**: New script for initializing the database and content.
- **test_quiz.py**: New script for testing quiz generation and evaluation.
- **templates/quiz.html**:
  - Made question count and rendering dynamic.
  - Replaced hardcoded JS data with Flask-passed data.
  - Added form and input logic for answer submission.
  - Improved validation and user experience.

---

## 7. How to Run the Project (Quick Guide)

1. **Set up the environment:**
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   brew install libomp  # (macOS only, for XGBoost)
   ```

2. **Initialize the database:**
   ```sh
   python3 init_db.py
   ```

3. **Run the application:**
   ```sh
   python3 main.py
   # Visit http://localhost:8000 in your browser
   ```

4. **(Optional) Test quiz functionality:**
   ```sh
   python3 test_quiz.py
   ```

---

## 8. Contact

For any issues or further improvements, please refer to this document or contact the project maintainer.

---

**End of Change Log** 