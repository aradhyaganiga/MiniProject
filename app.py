from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import secrets
import os
from datetime import datetime
import pickle
import numpy as np
from utils.ml_model import predict_compatibility, train_model, load_model
from utils.db_helper import init_db, get_db_connection, save_response, get_responses_by_link

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['DATABASE'] = 'data/compatibility.db'

# Initialize database on first run
init_db(app.config['DATABASE'])

@app.route('/')
def index():
    """Landing page - choose married/unmarried status"""
    return render_template('index.html')

@app.route('/select-gender', methods=['POST'])
def select_gender():
    """Store relationship status and redirect to gender selection"""
    relationship_status = request.form.get('status')  # 'married' or 'unmarried'
    return render_template('gender.html', status=relationship_status)

@app.route('/questions', methods=['POST'])
def questions():
    """Show questionnaire based on gender and status"""
    gender = request.form.get('gender')  # 'male' or 'female'
    status = request.form.get('status')  # 'married' or 'unmarried'
    
    # Get questions from database
    conn = get_db_connection(app.config['DATABASE'])
    cursor = conn.cursor()
    
    # Fetch questions appropriate for the gender
    cursor.execute('''
        SELECT id, question_text, domain, gender_specific 
        FROM questions 
        WHERE gender_specific = 'both' OR gender_specific = ?
        ORDER BY id
    ''', (gender,))
    
    questions = cursor.fetchall()
    
    # Fetch options for each question
    questions_with_options = []
    for q in questions:
        cursor.execute('''
            SELECT id, option_text, weight 
            FROM options 
            WHERE question_id = ?
            ORDER BY id
        ''', (q['id'],))
        options = cursor.fetchall()
        questions_with_options.append({
            'id': q['id'],
            'text': q['question_text'],
            'domain': q['domain'],
            'options': options
        })
    
    conn.close()
    
    return render_template('questions.html', 
                         questions=questions_with_options,
                         gender=gender,
                         status=status)

@app.route('/submit-answers', methods=['POST'])
def submit_answers():
    """Save user's answers and generate shareable link"""
    gender = request.form.get('gender')
    status = request.form.get('status')
    
    # Generate unique link token
    link_token = secrets.token_urlsafe(16)
    
    # Save to database
    conn = get_db_connection(app.config['DATABASE'])
    cursor = conn.cursor()
    
    # Create pair link entry
    cursor.execute('''
        INSERT INTO pair_links (link_token, relationship_status, created_at, is_complete)
        VALUES (?, ?, ?, ?)
    ''', (link_token, status, datetime.now().isoformat(), 0))
    
    pair_id = cursor.lastrowid
    
    # Save user responses
    answers = {}
    for key, value in request.form.items():
        if key.startswith('q_'):
            question_id = int(key.split('_')[1])
            option_id = int(value)
            answers[question_id] = option_id
            
            cursor.execute('''
                INSERT INTO responses (pair_id, user_number, question_id, option_id, response_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (pair_id, 1, question_id, option_id, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    # Generate shareable link
    partner_link = request.host_url + 'partner/' + link_token
    
    return render_template('link_generated.html', 
                         link=partner_link,
                         status=status)

@app.route('/partner/<link_token>')
def partner_questions(link_token):
    """Partner accesses questionnaire via shared link"""
    conn = get_db_connection(app.config['DATABASE'])
    cursor = conn.cursor()
    
    # Verify link exists and is not complete
    cursor.execute('''
        SELECT id, relationship_status, is_complete 
        FROM pair_links 
        WHERE link_token = ?
    ''', (link_token,))
    
    link_data = cursor.fetchone()
    
    if not link_data:
        conn.close()
        return render_template('error.html', message='Invalid link')
    
    if link_data['is_complete']:
        conn.close()
        return render_template('error.html', message='This link has already been used')
    
    # Get questions
    cursor.execute('''
        SELECT id, question_text, domain, gender_specific 
        FROM questions 
        ORDER BY id
    ''')
    
    questions = cursor.fetchall()
    
    questions_with_options = []
    for q in questions:
        cursor.execute('''
            SELECT id, option_text, weight 
            FROM options 
            WHERE question_id = ?
            ORDER BY id
        ''', (q['id'],))
        options = cursor.fetchall()
        questions_with_options.append({
            'id': q['id'],
            'text': q['question_text'],
            'domain': q['domain'],
            'options': options
        })
    
    conn.close()
    
    return render_template('partner_questions.html',
                         questions=questions_with_options,
                         link_token=link_token,
                         status=link_data['relationship_status'])

@app.route('/submit-partner-answers', methods=['POST'])
def submit_partner_answers():
    """Save partner's answers and redirect to results"""
    link_token = request.form.get('link_token')
    
    conn = get_db_connection(app.config['DATABASE'])
    cursor = conn.cursor()
    
    # Get pair_id from link_token
    cursor.execute('SELECT id FROM pair_links WHERE link_token = ?', (link_token,))
    pair_data = cursor.fetchone()
    pair_id = pair_data['id']
    
    # Save partner responses
    for key, value in request.form.items():
        if key.startswith('q_'):
            question_id = int(key.split('_')[1])
            option_id = int(value)
            
            cursor.execute('''
                INSERT INTO responses (pair_id, user_number, question_id, option_id, response_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (pair_id, 2, question_id, option_id, datetime.now().isoformat()))
    
    # Mark link as complete
    cursor.execute('UPDATE pair_links SET is_complete = 1 WHERE id = ?', (pair_id,))
    
    conn.commit()
    conn.close()
    
    # Redirect to results
    return redirect(url_for('show_results', link_token=link_token))

@app.route('/results/<link_token>')
def show_results(link_token):
    """Calculate and display compatibility/divorce prediction"""
    conn = get_db_connection(app.config['DATABASE'])
    cursor = conn.cursor()
    
    # Get pair data
    cursor.execute('''
        SELECT id, relationship_status 
        FROM pair_links 
        WHERE link_token = ?
    ''', (link_token,))
    pair_data = cursor.fetchone()
    pair_id = pair_data['id']
    status = pair_data['relationship_status']
    
    # Get both users' responses
    cursor.execute('''
        SELECT r.user_number, r.question_id, o.weight, q.domain
        FROM responses r
        JOIN options o ON r.option_id = o.id
        JOIN questions q ON r.question_id = q.id
        WHERE r.pair_id = ?
        ORDER BY r.user_number, r.question_id
    ''', (pair_id,))
    
    responses = cursor.fetchall()
    
    # Prepare features for ML model
    
    user1_scores = {}
    user2_scores = {}
    user1_counts = {}
    user2_counts = {}

    for resp in responses:
        domain = resp['domain']
        weight = resp['weight']

        if resp['user_number'] == 1:
            user1_scores[domain] = user1_scores.get(domain, 0) + weight
            user1_counts[domain] = user1_counts.get(domain, 0) + 1
        else:
            user2_scores[domain] = user2_scores.get(domain, 0) + weight
            user2_counts[domain] = user2_counts.get(domain, 0) + 1

# FIX: Calculate average score per domain (to keep scores in 0-4 range)
    for domain in user1_scores.keys():
        if user1_counts[domain] > 0:
            user1_scores[domain] = user1_scores[domain] / user1_counts[domain]

    for domain in user2_scores.keys():
        if user2_counts[domain] > 0:
            user2_scores[domain] = user2_scores[domain] / user2_counts[domain]
    
    # Make prediction
    prediction, probability, explanation = predict_compatibility(
        user1_scores, user2_scores, status
    )
    
    # Save results
    cursor.execute('''
        INSERT INTO results (pair_id, prediction_label, probability_score, explanation, predicted_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (pair_id, prediction, probability, explanation, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return render_template('result.html',
                         prediction=prediction,
                         probability=probability,
                         explanation=explanation,
                         status=status,
                         user1_scores=user1_scores,
                         user2_scores=user2_scores)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
