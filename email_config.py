# Email Configuration for Password Reset
# Update these settings to enable actual email sending

# Gmail Configuration (Recommended)
GMAIL_ENABLED = True  # Set to True to enable Gmail sending
GMAIL_EMAIL = "manismansuri24@gmail.com"  # Your Gmail address
GMAIL_PASSWORD = "jscl afnw eeep meqs"  # Your Gmail App Password

# Instructions for Gmail Setup:
# 1. Go to your Google Account settings
# 2. Enable 2-Factor Authentication
# 3. Go to Security > App passwords
# 4. Generate a new app password for "Mail"
# 5. Use that password (not your regular Gmail password)
# 6. Update GMAIL_EMAIL and GMAIL_PASSWORD above
# 7. Set GMAIL_ENABLED = True

# Alternative: Use a free email service like SendGrid or Mailgun
# For now, emails will be shown in the console for development 