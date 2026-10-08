# TODO: Add and Fix Login Page Functionality

## Steps to Complete:

1. **Update models.py**: Add `USERNAME_FIELD = 'email'` and `REQUIRED_FIELDS = ['username']` to the User model to allow login with email.

2. **Run Migrations**: Execute `python manage.py makemigrations` and `python manage.py migrate` to apply the model changes.

3. **Update forms.py**: Add a LoginForm class for handling login form validation.

4. **Update views.py**: Modify the login_view to use the LoginForm, handle authentication properly, and display error messages.

5. **Update login.html**: Extend base.html, render the form using the form object, and include error handling.

6. **Update register.html**: Change the 'name' input to 'username' to match the form fields.

7. **Test the Login Functionality**: Run the server and verify login works with email, redirects correctly, and handles errors.

## Progress:
- [x] Step 1
- [ ] Step 2 (Skipped - no migration needed)
- [x] Step 3
- [x] Step 4
- [x] Step 5
- [x] Step 6
- [x] Step 7 (Added styles and made login page standalone)

# Update Home Page UI to Match Screenshot

## Steps to Complete:

1. **Update base.html**: Replace Bootstrap navbar with custom purple navbar (logo "❤️ OrphaNet", Home, View Needs, conditional links). Remove Bootstrap CSS/JS.

2. **Refactor index.html**: Extend base.html, move content to block, update hero button to "View Needs" (green), third feature to "Track Impact & Proof".

3. **Update style.css**: Set hero button to green (#28a745), ensure auth button green.

4. **Test UI**: Run server, verify in browser that UI matches screenshot (purple theme, texts, green button).

## Progress:
- [x] Step 1
- [x] Step 2
- [x] Step 3
- [ ] Step 4
