# app.py

import os
from flask import Flask, render_template, request, redirect, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://newuser:password@localhost/test'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define a model for QA entries
class QAEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.String(255), nullable=False)
    tag = db.Column(db.String(50))  # Add new field for tag

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/file_upload')
def file_upload():
    return render_template('file_upload.html')

@app.route('/qa_entry_management')
def qa_entry_management():
    return render_template('qa_entry_management.html')

@app.route('/multi_turn_qa')
def multi_turn_qa():
    return render_template('multi_turn_qa.html')

# Example route to add a QA entry
@app.route('/add_qa_entry', methods=['POST'])
def add_qa_entry():
    if request.method == 'POST':
        question = request.form['question']
        answer = request.form['answer']
        tag = request.form['tag']  # Get tag from form
        
        new_entry = QAEntry(question=question, answer=answer, tag=tag)
        db.session.add(new_entry)
        db.session.commit()
        
    return redirect(url_for('qa_entry_management'))

@app.route('/qa_entries', methods=['GET'])
def get_qa_entries():
    qa_entries = QAEntry.query.all()
    return render_template('qa_entries.html', qa_entries=qa_entries)

# Example route to edit a QA entry
@app.route('/edit_qa_entry/<int:qa_entry_id>', methods=['GET', 'POST'])
def edit_qa_entry(qa_entry_id):
    qa_entry = QAEntry.query.get_or_404(qa_entry_id)
    if request.method == 'POST':
        qa_entry.question = request.form['question']
        qa_entry.answer = request.form['answer']
        qa_entry.tag = request.form['tag']
        db.session.commit()
        return redirect(url_for('get_qa_entries'))
    return render_template('edit_qa_entry.html', qa_entry=qa_entry)

# Example route to delete a QA entry
@app.route('/delete_qa_entry/<int:qa_entry_id>', methods=['POST'])
def delete_qa_entry(qa_entry_id):
    qa_entry = QAEntry.query.get_or_404(qa_entry_id)
    db.session.delete(qa_entry)
    db.session.commit()
    return redirect(url_for('get_qa_entries'))


    if __name__ == '__main__':
        app.run(debug=True)

if __name__=="__main__":
    app.run(host=os.getenv('IP', '0.0.0.0'), 
            port=int(os.getenv('PORT', 4444)))