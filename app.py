# app.py

import os
import csv  # Add this import statement
from io import StringIO  # Add this import statement
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:password@localhost/development'
app.config['SECRET_KEY'] = 'mysecretkey'  # Set a secret key for sessions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Define User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)

    # Implement UserMixin methods
    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(int(user_id))


# File upload logic
ALLOWED_EXTENSIONS = {'csv', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_csv(file_content):
    try:
        parsed_data = []
        rows = csv.reader(StringIO(file_content))
        next(rows)
        for row in rows:
            if len(row) != 3:
                return False, "File does not have the expected number of columns"
            parsed_data.append(row)
        return True, parsed_data
    except Exception as e:
        return False, f"Error parsing CSV file: {str(e)}"

def parse_txt(file_content):
    try:
        parsed_data = []
        lines = file_content.split('\n')
        question = None
        answer = None
        tags = None
        for line in lines:
            if line.startswith('question:'):
                if question is not None:
                    parsed_data.append((question, answer, tags))
                question = line.split('question:')[1].strip()
            elif line.startswith('answer:'):
                answer = line.split('answer:')[1].strip()
            elif line.startswith('tags:'):
                tags = line.split('tags:')[1].strip()
        if question and answer and tags:
            parsed_data.append((question, answer, tags))
        else:
            return False, "File format is not correct"
        return True, parsed_data
    except Exception as e:
        return False, f"Error parsing TXT file: {str(e)}"

def insert_into_database(data):
    if data:
        try:
            for row in data:
                question, answer, tags_str = row
                # Split tags string by comma and remove leading/trailing spaces
                tag_names = [tag.strip() for tag in tags_str.split(',')]
                tags = []
                for tag_name in tag_names:
                    # Check if tag already exists in the database
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        # If tag does not exist, create a new one
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    tags.append(tag)
                new_entry = QAEntry(question=question, answer=answer, tags=tags)
                db.session.add(new_entry)
            db.session.commit()
            return True, "Data inserted into the database successfully"  # Return success and a message
        except Exception as e:
            db.session.rollback()
            return False, f"Error inserting data into the database: {str(e)}"  # Return failure and an error message
    else:
        return False, "No data provided"  # Return failure and a message if no data is provided


@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('files')
        if not files:
            return jsonify({'error': 'No files provided'}), 400
        
        file_contents = {}
        for file in files:
            if file and allowed_file(file.filename):
                file_contents[file.filename] = file.read().decode('utf-8')
            else:
                return jsonify({'error': 'Only CSV and TXT files are allowed'}), 400
        
        if not file_contents:
            return jsonify({'error': 'No valid files provided'}), 400
        
        success = False
        message = None

        for file_name, file_content in file_contents.items():
            if file_name.endswith('.csv'):
                success, parsed_data = parse_csv(file_content)
            elif file_name.endswith('.txt'):
                success, parsed_data = parse_txt(file_content)
            else:
                message = "Only CSV and TXT files are allowed"
                break
            
            if success:
                success, message = insert_into_database(parsed_data)
                if not success:
                    break
            else:
                message = parsed_data
                break

        if success:
            return jsonify({'message': message}), 200
        else:
            return jsonify({'error': message}), 400


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
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

# Define Tag model
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

# Association table for many-to-many relationship
qa_entry_tags = db.Table('qa_entry_tags',
    db.Column('qa_entry_id', db.Integer, db.ForeignKey('qa_entry.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

# Define QAEntry model with many-to-many relationship to Tag
class QAEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.String(255), nullable=False)
    tags = db.relationship('Tag', secondary=qa_entry_tags, backref='qa_entries', lazy='dynamic')
    date = db.Column(db.Date, default=datetime.utcnow)
    time = db.Column(db.Time, default=datetime.utcnow().time())

# Example route to add a QA entry
@app.route('/add_qa_entry', methods=['POST'])
@login_required
def add_qa_entry():
    if request.method == 'POST':
        question = request.form['question']
        answer = request.form['answer']
        tag_names = request.form.getlist('tags')  # Retrieve multiple tags
        tags = [Tag.query.filter_by(name=name).first() or Tag(name=name) for name in tag_names]
        new_entry = QAEntry(question=question, answer=answer, tags=tags)
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
        tag_names = request.form.getlist('tags')  # Retrieve multiple tags
        tags = [Tag.query.filter_by(name=name).first() or Tag(name=name) for name in tag_names]
        qa_entry.tags = tags
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

# Route to display QA entries
@app.route('/qa_entries', methods=['GET'])
@login_required
def get_qa_entries():
    qa_entries = QAEntry.query.all()
    return render_template('qa_entries.html', qa_entries=qa_entries)


if __name__ == "__main__":
    app.run(host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 4444)))
