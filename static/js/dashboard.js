// Dashboard JavaScript functionality

let predictionsChart, progressChart, difficultyChart;

function initializeDashboard(data) {
    // Initialize all charts
    initializePredictionsChart(data.predictions);
    initializeProgressChart(data.recentScores);
    initializeDifficultyChart(data.quizStats);
    
    // Setup real-time updates
    setupRealTimeUpdates();
    
    // Setup interactive elements
    setupInteractiveElements();
}

function initializePredictionsChart(predictions) {
    const ctx = document.getElementById('predictionsChart');
    if (!ctx) return;
    
    const modelLabels = [];
    const modelScores = [];
    const colors = ['#dc3545', '#0dcaf0', '#ffc107'];
    
    Object.entries(predictions).forEach(([model, score], index) => {
        let displayName = model;
        if (model === 'random_forest') displayName = 'Random Forest';
        else if (model === 'xgboost') displayName = 'XGBoost';
        else if (model === 'neural_network') displayName = 'Neural Network';
        
        modelLabels.push(displayName);
        modelScores.push(score);
    });
    
    predictionsChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: modelLabels,
            datasets: [{
                data: modelScores,
                backgroundColor: colors,
                borderColor: colors.map(color => color + '80'),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                },
                title: {
                    display: true,
                    text: 'Model Predictions Comparison',
                    font: {
                        size: 16
                    }
                }
            },
            animation: {
                animateScale: true,
                animateRotate: true
            }
        }
    });
}

function initializeProgressChart(recentScores) {
    const ctx = document.getElementById('progressChart');
    if (!ctx) return;
    
    const labels = recentScores.map((_, index) => `Quiz ${index + 1}`);
    
    progressChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Score %',
                data: recentScores,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#0d6efd',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Recent Quiz Performance',
                    font: {
                        size: 16
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            elements: {
                point: {
                    hoverRadius: 8
                }
            },
            animation: {
                duration: 2000,
                easing: 'easeInOutQuart'
            }
        }
    });
}

function initializeDifficultyChart(quizStats) {
    const ctx = document.getElementById('difficultyChart');
    if (!ctx) return;
    
    const difficultyBreakdown = quizStats.difficulty_breakdown || {};
    const labels = Object.keys(difficultyBreakdown).map(level => level.charAt(0).toUpperCase() + level.slice(1));
    const data = Object.values(difficultyBreakdown).map(item => item.count);
    const colors = ['#198754', '#ffc107', '#dc3545'];
    
    difficultyChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderColor: colors.map(color => color + '80'),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        usePointStyle: true
                    }
                },
                title: {
                    display: true,
                    text: 'Quiz Difficulty Distribution',
                    font: {
                        size: 14
                    }
                }
            },
            animation: {
                animateScale: true,
                animateRotate: true
            }
        }
    });
}

function setupRealTimeUpdates() {
    // Refresh predictions every 30 seconds
    setInterval(() => {
        updatePredictions();
    }, 30000);
    
    // Update quiz statistics every 60 seconds
    setInterval(() => {
        updateQuizStatistics();
    }, 60000);
}

function updatePredictions() {
    fetch('/api/model_predictions')
        .then(response => response.json())
        .then(data => {
            if (predictionsChart) {
                const modelScores = [];
                Object.entries(data).forEach(([model, score]) => {
                    modelScores.push(score);
                });
                
                predictionsChart.data.datasets[0].data = modelScores;
                predictionsChart.update('none');
            }
        })
        .catch(error => {
            console.error('Error updating predictions:', error);
        });
}

function updateQuizStatistics() {
    fetch('/api/quiz_stats')
        .then(response => response.json())
        .then(data => {
            // Update progress chart
            if (progressChart && data.recent_scores) {
                const labels = data.recent_scores.map((_, index) => `Quiz ${index + 1}`);
                progressChart.data.labels = labels;
                progressChart.data.datasets[0].data = data.recent_scores;
                progressChart.update('none');
            }
            
            // Update difficulty chart
            if (difficultyChart && data.difficulty_breakdown) {
                const labels = Object.keys(data.difficulty_breakdown).map(level => 
                    level.charAt(0).toUpperCase() + level.slice(1)
                );
                const chartData = Object.values(data.difficulty_breakdown).map(item => item.count);
                
                difficultyChart.data.labels = labels;
                difficultyChart.data.datasets[0].data = chartData;
                difficultyChart.update('none');
            }
        })
        .catch(error => {
            console.error('Error updating quiz statistics:', error);
        });
}

function setupInteractiveElements() {
    // Add loading states for buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            if (this.type === 'submit' || this.href) {
                this.classList.add('loading');
                const originalText = this.innerHTML;
                this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
                
                setTimeout(() => {
                    this.classList.remove('loading');
                    this.innerHTML = originalText;
                }, 2000);
            }
        });
    });
    
    // Add hover effects to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Add smooth scrolling to anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Utility functions
function formatScore(score) {
    return Math.round(score * 10) / 10;
}

function getScoreColor(score) {
    if (score >= 80) return '#198754'; // success
    if (score >= 60) return '#ffc107'; // warning
    return '#dc3545'; // danger
}

function animateValue(element, start, end, duration) {
    const startTime = performance.now();
    const updateValue = (currentTime) => {
        const elapsedTime = currentTime - startTime;
        const progress = Math.min(elapsedTime / duration, 1);
        const value = start + (end - start) * progress;
        element.textContent = Math.round(value);
        
        if (progress < 1) {
            requestAnimationFrame(updateValue);
        }
    };
    requestAnimationFrame(updateValue);
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fade-in');
        }, index * 100);
    });
    
    // Animate statistics values
    const statValues = document.querySelectorAll('.stat-value');
    statValues.forEach(element => {
        const finalValue = parseInt(element.textContent);
        element.textContent = '0';
        setTimeout(() => {
            animateValue(element, 0, finalValue, 1000);
        }, 500);
    });
});

// Handle retrain models button
function retrainModels() {
    const button = document.getElementById('retrainButton');
    if (button) {
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Retraining...';
        
        fetch('/api/retrain_models', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update predictions after retraining
                updatePredictions();
                button.innerHTML = '<i data-feather="refresh-cw"></i> Retrained Successfully';
                button.classList.add('btn-success');
                button.classList.remove('btn-primary');
                
                setTimeout(() => {
                    button.disabled = false;
                    button.innerHTML = '<i data-feather="refresh-cw"></i> Retrain Models';
                    button.classList.add('btn-primary');
                    button.classList.remove('btn-success');
                    feather.replace();
                }, 3000);
            } else {
                button.innerHTML = '<i data-feather="alert-circle"></i> Retrain Failed';
                button.classList.add('btn-danger');
                button.classList.remove('btn-primary');
                
                setTimeout(() => {
                    button.disabled = false;
                    button.innerHTML = '<i data-feather="refresh-cw"></i> Retrain Models';
                    button.classList.add('btn-primary');
                    button.classList.remove('btn-danger');
                    feather.replace();
                }, 3000);
            }
        })
        .catch(error => {
            console.error('Error retraining models:', error);
            button.disabled = false;
            button.innerHTML = '<i data-feather="alert-circle"></i> Error';
            button.classList.add('btn-danger');
            button.classList.remove('btn-primary');
            feather.replace();
        });
    }
}
