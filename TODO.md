# Task: Update login to dummy email/password validation

## Steps:
1. [x] Edit templates/login.html: Update form to use 'email' field, change labels/placeholders accordingly.
2. [x] Edit app.py: Remove USERS dict and @app.before_request decorator, update /login route logic for '@' in email check.
3. [x] Restart Flask server with `python app.py`
4. [x] Test login screen with email containing '@' and any password.
5. [x] Verify no auth protection, direct access to /predict works.
6. [x] Mark complete and attempt_completion.

✅ All steps completed.
