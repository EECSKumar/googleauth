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
        
        new_entry = QAEntry(question=question, answer=answer)
        db.session.add(new_entry)
        db.session.commit()
        
    return redirect(url_for('qa_entry_management'))

# Example route to edit a QA entry
@app.route('/edit_qa_entry/<int:id>', methods=['GET', 'POST'])
def edit_qa_entry(id):
    entry = QAEntry.query.get(id)

    if request.method == 'POST':
        entry.question = request.form['question']
        entry.answer = request.form['answer']
        db.session.commit()
        
        return redirect(url_for('qa_entry_management'))
    
    return render_template('edit_qa_entry.html', entry=entry)

# Example route to delete a QA entry
@app.route('/delete_qa_entry/<int:id>')
def delete_qa_entry(id):
    entry = QAEntry.query.get(id)
    db.session.delete(entry)
    db.session.commit()
    
    return redirect(url_for('qa_entry_management'))

    if __name__ == '__main__':
        app.run(debug=True)


if __name__=="__main__":
    app.run(host=os.getenv('IP', '0.0.0.0'), 
            port=int(os.getenv('PORT', 4444)))