import sqlite3
import os

def get_db_connection(db_path):
    """Create database connection with row factory"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path):
    """Initialize database with schema and sample data"""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript('''
        -- Table: pair_links (stores generated links for couples)
        CREATE TABLE IF NOT EXISTS pair_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_token TEXT UNIQUE NOT NULL,
            relationship_status TEXT NOT NULL,  -- 'married' or 'unmarried'
            created_at TEXT NOT NULL,
            is_complete INTEGER DEFAULT 0,
            CONSTRAINT chk_status CHECK (relationship_status IN ('married', 'unmarried'))
        );
        
        -- Table: questions (all questionnaire questions)
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL,
            domain TEXT NOT NULL,  -- e.g., 'communication', 'finance', 'intimacy'
            gender_specific TEXT DEFAULT 'both',  -- 'male', 'female', or 'both'
            CONSTRAINT chk_gender CHECK (gender_specific IN ('male', 'female', 'both'))
        );
        
        -- Table: options (answer options for each question with weights)
        CREATE TABLE IF NOT EXISTS options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            option_text TEXT NOT NULL,
            weight INTEGER NOT NULL,  -- numeric weight for ML model
            FOREIGN KEY (question_id) REFERENCES questions(id)
        );
        
        -- Table: responses (stores user answers)
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pair_id INTEGER NOT NULL,
            user_number INTEGER NOT NULL,  -- 1 or 2
            question_id INTEGER NOT NULL,
            option_id INTEGER NOT NULL,
            response_time TEXT NOT NULL,
            FOREIGN KEY (pair_id) REFERENCES pair_links(id),
            FOREIGN KEY (question_id) REFERENCES questions(id),
            FOREIGN KEY (option_id) REFERENCES options(id),
            CONSTRAINT chk_user CHECK (user_number IN (1, 2))
        );
        
        -- Table: results (stores prediction results)
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pair_id INTEGER NOT NULL,
            prediction_label TEXT NOT NULL,  -- e.g., 'High Compatibility', 'Divorce Risk'
            probability_score REAL NOT NULL,
            explanation TEXT,
            predicted_at TEXT NOT NULL,
            FOREIGN KEY (pair_id) REFERENCES pair_links(id)
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_link_token ON pair_links(link_token);
        CREATE INDEX IF NOT EXISTS idx_responses_pair ON responses(pair_id);
        CREATE INDEX IF NOT EXISTS idx_options_question ON options(question_id);
    ''')
    
    # Insert sample questions if not exists
    cursor.execute('SELECT COUNT(*) as cnt FROM questions')
    if cursor.fetchone()[0] == 0:
        insert_sample_questions(cursor)
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {db_path}")

def insert_sample_questions(cursor):
    """Insert sample questionnaire questions and options"""
    
    questions_data = [
        # Communication Domain
        (1, "How often do you and your partner have meaningful conversations?", "communication", "both"),
        (2, "When you disagree, how do you typically resolve conflicts?", "communication", "both"),
        (3, "How comfortable are you expressing your feelings to your partner?", "communication", "both"),
        
        # Trust & Honesty Domain
        (4, "How much do you trust your partner with important decisions?", "trust", "both"),
        (5, "How often do you feel the need to check your partner's phone or social media?", "trust", "both"),
        
        # Financial Domain
        (6, "How do you handle financial decisions in your relationship?", "finance", "both"),
        (7, "How often do you argue about money?", "finance", "both"),
        
        # Intimacy & Affection Domain
        (8, "How satisfied are you with physical intimacy in your relationship?", "intimacy", "both"),
        (9, "How often do you express affection (hugs, kisses, compliments)?", "intimacy", "both"),
        
        # Family & Future Domain
        (10, "Are you aligned on having children (or parenting style if you have kids)?", "family", "both"),
        (11, "How well do you get along with each other's families?", "family", "both"),
        
        # Personal Growth Domain
        (12, "Does your partner support your personal goals and ambitions?", "personal_growth", "both"),
        (13, "How much personal space/independence do you have in the relationship?", "personal_growth", "both"),
        
        # Commitment Domain
        (14, "How committed do you feel to making this relationship work?", "commitment", "both"),
        (15, "Have you thought about ending the relationship in the past 6 months?", "commitment", "both"),
    ]
    
    for q_id, text, domain, gender in questions_data:
        cursor.execute('''
            INSERT INTO questions (id, question_text, domain, gender_specific)
            VALUES (?, ?, ?, ?)
        ''', (q_id, text, domain, gender))
    
    # Insert options for each question (4 options per question)
    options_data = [
        # Q1: meaningful conversations
        (1, "Daily - we talk about everything", 4),
        (1, "Several times a week", 3),
        (1, "Occasionally", 2),
        (1, "Rarely or never", 1),
        
        # Q2: conflict resolution
        (2, "We discuss calmly and find compromise", 4),
        (2, "We eventually resolve after cooling down", 3),
        (2, "We avoid discussing issues", 2),
        (2, "We argue intensely/yell", 1),
        
        # Q3: expressing feelings
        (3, "Very comfortable - I share everything", 4),
        (3, "Mostly comfortable", 3),
        (3, "Somewhat uncomfortable", 2),
        (3, "Very uncomfortable or afraid", 1),
        
        # Q4: trust with decisions
        (4, "Complete trust", 4),
        (4, "Mostly trust", 3),
        (4, "Some doubts", 2),
        (4, "Little to no trust", 1),
        
        # Q5: checking partner's devices
        (5, "Never - full trust", 4),
        (5, "Rarely", 3),
        (5, "Sometimes", 2),
        (5, "Often or always", 1),
        
        # Q6: financial decisions
        (6, "We plan and decide together", 4),
        (6, "We discuss major expenses", 3),
        (6, "We mostly handle separately", 2),
        (6, "Constant disagreements about money", 1),
        
        # Q7: money arguments
        (7, "Never or very rarely", 4),
        (7, "Occasionally", 3),
        (7, "Frequently", 2),
        (7, "All the time", 1),
        
        # Q8: physical intimacy satisfaction
        (8, "Very satisfied", 4),
        (8, "Mostly satisfied", 3),
        (8, "Somewhat dissatisfied", 2),
        (8, "Very dissatisfied", 1),
        
        # Q9: expressing affection
        (9, "Daily", 4),
        (9, "Several times a week", 3),
        (9, "Occasionally", 2),
        (9, "Rarely or never", 1),
        
        # Q10: alignment on children
        (10, "Fully aligned", 4),
        (10, "Mostly aligned", 3),
        (10, "Some disagreements", 2),
        (10, "Major disagreements", 1),
        
        # Q11: family relationships
        (11, "Very well - no issues", 4),
        (11, "Generally well", 3),
        (11, "Some tension", 2),
        (11, "Poorly - major conflicts", 1),
        
        # Q12: support for goals
        (12, "Fully supportive", 4),
        (12, "Mostly supportive", 3),
        (12, "Somewhat supportive", 2),
        (12, "Not supportive", 1),
        
        # Q13: personal space
        (13, "Healthy balance", 4),
        (13, "Mostly good", 3),
        (13, "Too much or too little space", 2),
        (13, "No independence/space", 1),
        
        # Q14: commitment level
        (14, "Fully committed - 100%", 4),
        (14, "Very committed", 3),
        (14, "Somewhat committed", 2),
        (14, "Not committed", 1),
        
        # Q15: thoughts of ending relationship
        (15, "Never", 4),
        (15, "Once or twice in passing", 3),
        (15, "Several times", 2),
        (15, "Frequently", 1),
    ]
    
    for question_id, option_text, weight in options_data:
        cursor.execute('''
            INSERT INTO options (question_id, option_text, weight)
            VALUES (?, ?, ?)
        ''', (question_id, option_text, weight))

def save_response(db_path, pair_id, user_number, question_id, option_id, response_time):
    """Save a single response"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO responses (pair_id, user_number, question_id, option_id, response_time)
        VALUES (?, ?, ?, ?, ?)
    ''', (pair_id, user_number, question_id, option_id, response_time))
    conn.commit()
    conn.close()

def get_responses_by_link(db_path, link_token):
    """Get all responses for a pair by link token"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.*, q.domain, o.weight
        FROM responses r
        JOIN pair_links pl ON r.pair_id = pl.id
        JOIN questions q ON r.question_id = q.id
        JOIN options o ON r.option_id = o.id
        WHERE pl.link_token = ?
    ''', (link_token,))
    responses = cursor.fetchall()
    conn.close()
    return responses
