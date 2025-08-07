import os

# Email Configuration for Password Reset
# For local development, you can hardcode your credentials below.
# For deployment, use environment variables for security.

GMAIL_ENABLED = True  # Set to True to enable Gmail sending
GMAIL_EMAIL = "manismansuri24@gmail.com"  # Your Gmail address
GMAIL_PASSWORD = "jscl afnw eeep meqs"  # Your Gmail App Password

# For deployment, uncomment the following lines and comment out the above 3 lines:
# GMAIL_ENABLED = os.getenv('GMAIL_ENABLED', 'False') == 'True'
# GMAIL_EMAIL = os.getenv('GMAIL_EMAIL')
# GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')

# Instructions for Gmail Setup:
# 1. Go to your Google Account settings
# 2. Enable 2-Factor Authentication
# 3. Go to Security > App passwords
# 4. Generate a new app password for "Mail"
# 5. Use that password (not your regular Gmail password)
# 6. Set GMAIL_EMAIL and GMAIL_PASSWORD above or as environment variables
# 7. Set GMAIL_ENABLED=True

# Alternative: Use a free email service like SendGrid or Mailgun
# For now, emails will be shown in the console for development if not configured 