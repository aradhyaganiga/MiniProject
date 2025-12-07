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
        (4, "How well does your partner listen when you share your concerns?", "communication", "both"),
        (5, "Do you feel comfortable discussing difficult topics with your partner?", "communication", "both"),
        (6, "How often do you misunderstand each other's intentions?", "communication", "both"),
        
        # Trust & Honesty Domain
        (7, "How much do you trust your partner with important decisions?", "trust", "both"),
        (8, "How often do you feel the need to check your partner's phone or social media?", "trust", "both"),
        (9, "How transparent are you with your partner about your daily activities?", "trust", "both"),
        (10, "Do you feel secure in your partner's commitment to you?", "trust", "both"),
        
        # Financial Domain
        (11, "How do you handle financial decisions in your relationship?", "finance", "both"),
        (12, "How often do you argue about money?", "finance", "both"),
        (13, "Do you and your partner have similar spending habits?", "finance", "both"),
        (14, "How comfortable are you discussing financial goals together?", "finance", "both"),
        
        # Intimacy & Affection Domain
        (15, "How satisfied are you with physical intimacy in your relationship?", "intimacy", "both"),
        (16, "How often do you express affection (hugs, kisses, compliments)?", "intimacy", "both"),
        (17, "How satisfied are you with the emotional intimacy in your relationship?", "intimacy", "both"),
        (18, "Do you feel your partner understands your emotional needs?", "intimacy", "both"),
        
        # Family & Future Domain
        (19, "Are you aligned on having children (or parenting style if you have kids)?", "family", "both"),
        (20, "How well do you get along with each other's families?", "family", "both"),
        (21, "How aligned are you on where to live (near family vs. independent)?", "family", "both"),
        (22, "Do you share similar cultural or religious values?", "family", "both"),
        
        # Personal Growth Domain
        (23, "Does your partner support your personal goals and ambitions?", "personal_growth", "both"),
        (24, "How much personal space/independence do you have in the relationship?", "personal_growth", "both"),
        (25, "Does your relationship encourage you to become a better person?", "personal_growth", "both"),
        (26, "How well do you balance relationship time with personal hobbies?", "personal_growth", "both"),
        
        # Commitment Domain
        (27, "How committed do you feel to making this relationship work?", "commitment", "both"),
        (28, "Have you thought about ending the relationship in the past 6 months?", "commitment", "both"),
        (29, "How often do you discuss your future together?", "commitment", "both"),
        (30, "Are you both on the same page about long-term relationship goals?", "commitment", "both"),
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

        # Q4: listening quality
        (4, "Excellent - fully attentive", 4),
        (4, "Good - mostly listens", 3),
        (4, "Fair - sometimes distracted", 2),
        (4, "Poor - rarely listens", 1),

        # Q5: difficult topics
        (5, "Very comfortable - we discuss everything", 4),
        (5, "Mostly comfortable", 3),
        (5, "Somewhat uncomfortable", 2),
        (5, "Very uncomfortable - we avoid them", 1),

        # Q6: misunderstandings
        (6, "Rarely or never", 4),
        (6, "Occasionally", 3),
        (6, "Frequently", 2),
        (6, "Very often", 1),
        
        # Q7: trust with decisions
        (7, "Complete trust", 4),
        (7, "Mostly trust", 3),
        (7, "Some doubts", 2),
        (7, "Little to no trust", 1),
        
        # Q8: checking partner's devices
        (8, "Never - full trust", 4),
        (8, "Rarely", 3),
        (8, "Sometimes", 2),
        (8, "Often or always", 1),

        # Q9: transparency
        (9, "Complete transparency", 4),
        (9, "Mostly transparent", 3),
        (9, "Somewhat secretive", 2),
        (9, "Very secretive", 1),

        # Q10: security in commitment
        (10, "Very secure", 4),
        (10, "Mostly secure", 3),
        (10, "Somewhat insecure", 2),
        (10, "Very insecure", 1),
        
        # Q11: financial decisions
        (11, "We plan and decide together", 4),
        (11, "We discuss major expenses", 3),
        (11, "We mostly handle separately", 2),
        (11, "Constant disagreements about money", 1),
        
        # Q12: money arguments
        (12, "Never or very rarely", 4),
        (12, "Occasionally", 3),
        (12, "Frequently", 2),
        (12, "All the time", 1),

        # Q13: spending habits
        (13, "Very similar", 4),
        (13, "Mostly similar", 3),
        (13, "Somewhat different", 2),
        (13, "Very different", 1),

        # Q14: financial discussions
        (14, "Very comfortable", 4),
        (14, "Mostly comfortable", 3),
        (14, "Somewhat uncomfortable", 2),
        (14, "Very uncomfortable", 1),
        
        # Q15: physical intimacy satisfaction
        (15, "Very satisfied", 4),
        (15, "Mostly satisfied", 3),
        (15, "Somewhat dissatisfied", 2),
        (15, "Very dissatisfied", 1),
        
        # Q16: expressing affection
        (16, "Daily", 4),
        (16, "Several times a week", 3),
        (16, "Occasionally", 2),
        (16, "Rarely or never", 1),

        # Q17: emotional intimacy
        (17, "Very satisfied", 4),
        (17, "Mostly satisfied", 3),
        (17, "Somewhat dissatisfied", 2),
        (17, "Very dissatisfied", 1),

        # Q18: understanding emotional needs
        (18, "Completely understands", 4),
        (18, "Mostly understands", 3),
        (18, "Somewhat understands", 2),
        (18, "Doesn't understand", 1),
        
        # Q19: alignment on children
        (19, "Fully aligned", 4),
        (19, "Mostly aligned", 3),
        (19, "Some disagreements", 2),
        (19, "Major disagreements", 1),
        
        # Q20: family relationships
        (20, "Very well - no issues", 4),
        (20, "Generally well", 3),
        (20, "Some tension", 2),
        (20, "Poorly - major conflicts", 1),

        # Q21: living location alignment
        (21, "Fully aligned", 4),
        (21, "Mostly aligned", 3),
        (21, "Some disagreement", 2),
        (21, "Major disagreement", 1),

        # Q22: cultural/religious values
        (22, "Very similar", 4),
        (22, "Mostly similar", 3),
        (22, "Somewhat different", 2),
        (22, "Very different", 1),
        
        # Q23: support for goals
        (23, "Fully supportive", 4),
        (23, "Mostly supportive", 3),
        (23, "Somewhat supportive", 2),
        (23, "Not supportive", 1),
        
        # Q24: personal space
        (24, "Healthy balance", 4),
        (24, "Mostly good", 3),
        (24, "Too much or too little space", 2),
        (24, "No independence/space", 1),

        # Q25: personal growth encouragement
        (25, "Strongly encourages growth", 4),
        (25, "Somewhat encourages", 3),
        (25, "Neutral", 2),
        (25, "Holds me back", 1),

        # Q26: balance of time
        (26, "Perfect balance", 4),
        (26, "Good balance", 3),
        (26, "Struggling to balance", 2),
        (26, "No balance", 1),
        
        # Q27: commitment level
        (27, "Fully committed - 100%", 4),
        (27, "Very committed", 3),
        (27, "Somewhat committed", 2),
        (27, "Not committed", 1),
        
        # Q28: thoughts of ending relationship
        (28, "Never", 4),
        (28, "Once or twice in passing", 3),
        (28, "Several times", 2),
        (28, "Frequently", 1),

        # Q29: future discussions
        (29, "Regularly - we plan together", 4),
        (29, "Sometimes", 3),
        (29, "Rarely", 2),
        (29, "Never", 1),

        # Q30: long-term goals alignment
        (30, "Completely aligned", 4),
        (30, "Mostly aligned", 3),
        (30, "Somewhat different", 2),
        (30, "Very different goals", 1),
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
