# app.py

import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:password@localhost/development'
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = 'mysecretkey'
migrate = Migrate(app, db)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Define a User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)

    # Implement the UserMixin methods
    def is_active(self):
        return True  # Assuming all users are active, adjust as needed

    def is_authenticated(self):
        return True  # Assuming all users are authenticated, adjust as needed

    def is_anonymous(self):
        return False  # Assuming we don't have anonymous users

    def get_id(self):
        return str(self.id)  # Return the user ID as a string



# Callback to reload the user object
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            # Login successful
            login_user(user)
            return redirect(url_for('get_qa_entries'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')




# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists.', 'error')
        else:
            # Hash the password before storing it
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, email=email, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful. You can now login.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Protected route for QA entry management
@app.route('/qa_entry_management')
@login_required
def qa_entry_management():
    return render_template('qa_entry_management.html')


# Define a model for QA entries
class QAEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.String(255), nullable=False)
    tag = db.Column(db.String(50))  # Add new field for tag
    date = db.Column(db.Date, default=datetime.utcnow)  # Column for date
    time = db.Column(db.Time, default=datetime.utcnow().time())  # Column for time


# Example route to add a QA entry
@app.route('/add_qa_entry', methods=['POST'])
@login_required
def add_qa_entry():
    if request.method == 'POST':
        question = request.form['question']
        answer = request.form['answer']
        tag = request.form['tag']
        date = datetime.utcnow().date()  # Update date with current date
        time = datetime.utcnow().time()  # Update time with current time
        
        new_entry = QAEntry(question=question, answer=answer, tag=tag, date=date, time=time)  # Pass created_at to the constructor
        db.session.add(new_entry)
        db.session.commit()
        
    return redirect(url_for('qa_entry_management'))

# Example route to edit a QA entry
@app.route('/edit_qa_entry/<int:qa_entry_id>', methods=['GET', 'POST'])
@login_required
def edit_qa_entry(qa_entry_id):
    qa_entry = QAEntry.query.get_or_404(qa_entry_id)
    if request.method == 'POST':
        qa_entry.question = request.form['question']
        qa_entry.answer = request.form['answer']
        qa_entry.tag = request.form['tag']
        qa_entry.date = datetime.utcnow().date()  # Update date with current date
        qa_entry.time = datetime.utcnow().time()  # Update time with current time
        db.session.commit()
        return redirect(url_for('get_qa_entries'))
    return render_template('edit_qa_entry.html', qa_entry=qa_entry)


# Example route to delete a QA entry
@app.route('/delete_qa_entry/<int:qa_entry_id>', methods=['POST'])
@login_required
def delete_qa_entry(qa_entry_id):
    qa_entry = QAEntry.query.get_or_404(qa_entry_id)
    db.session.delete(qa_entry)
    db.session.commit()
    return redirect(url_for('get_qa_entries'))

@app.route('/qa_entries', methods=['GET'])
@login_required
def get_qa_entries():
    qa_entries = QAEntry.query.all()
    return render_template('qa_entries.html', qa_entries=qa_entries)

if __name__=="__main__":
    app.run(host=os.getenv('IP', '0.0.0.0'), 
            port=int(os.getenv('PORT', 4444)))
    















