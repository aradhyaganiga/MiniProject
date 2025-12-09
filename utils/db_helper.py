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
        (3, "How do you typically handle disagreements?", "communication", "both"),
        (4, "How do you respond when your partner shares a personal problem?", "communication", "both"),
        (5, "If your partner misunderstands you, what you will do usually?", "communication", "both"),
        (6, "When making an important decision together, what you will prefer?", "communication", "both"),
        
        # Trust & Honesty Domain
        (7, "If a partner criticizes your family in an argument, what you will do?", "trust", "both"),
        (8, "If your partner wants to spend a weekend away with friends, do you allow?", "trust", "both"),
        (9, "If your partner deletes text messages regularly. How you feel?", "trust", "both"),
        (10, "A former romantic interest reaches out to your partner.What they should do?", "trust", "both"),
        
        # Financial Domain
        (11, "Which best describes your financial style?", "finance", "both"),
        (12, "What's your view on helping siblings or family financially?", "finance", "both"),
        (13, "How would you feel if your partner earned significantly more?", "finance", "both"),
        (14, "One of you wants to invest in stocks; the other prefers property. What you prefer?", "finance", "both"),
        
        # Intimacy & Affection Domain
        (15, "What are your expectations regarding intimacy?", "intimacy", "both"),
        (16, "If one partner's intimacy drive decreases due to stress, the other should?", "intimacy", "both"),
        (17, "How important is trying new things in your intimate life?", "intimacy", "both"),
        (18, "How do you view physical affection in between daily activities?", "intimacy", "both"),
        
        # Family & Future Domain
        (19, "What role do you expect your parents to play in your married life?", "family", "both"),
        (20, "Your parents want to live with you after retirement. Your partner disagrees. what do u do?", "family", "both"),
        (21, "How aligned are you on where to live (near family vs. independent)?", "family", "both"),
        (22, "Do you share similar cultural or religious values?", "family", "both"),
        
        # Personal Growth Domain
        (23, "What do you consider the primary goal of marriage?", "personal_growth", "both"),
        (24, "Your partner wants to adopt a pet. You don't. what you will do?", "personal_growth", "both"),
        (25, "what does successful marriage mean to you?", "personal_growth", "both"),
        (26, "You and partner want different holiday destinations.what do you do?", "personal_growth", "both"),
        
        # Commitment Domain
        (27, "What are your views on having children?", "commitment", "both"),
        (28, "How would you approach relocating for a job opportunity?", "commitment", "both"),
        (29, "How do you believe household chores should be divided?", "commitment", "both"),
        (30, "When your partner is sick, what is next step of yours?", "commitment", "both"),
    ]
    
    for q_id, text, domain, gender in questions_data:
        cursor.execute('''
            INSERT INTO questions (id, question_text, domain, gender_specific)
            VALUES (?, ?, ?, ?)
        ''', (q_id, text, domain, gender))
    
    # Insert options for each question (4 options per question)
    options_data = [
        # Q1: meaningful conversations
        (1, "Daily - We talk deeply every day", 4),
        (1, "Sometimes - A few times a week", 3),
        (1, "Rarely - Less than once a week", 2),
        (1, "Never - We don't talk about important things", 1),
        
        # Q2: conflict resolution
        (2, "We discuss calmly and always find solutions", 4),
        (2, "We discuss calmly but struggle to compromise", 3),
        (2, "We avoid conflicts completely", 2),
        (2, "We yell and don't resolve issues", 1),
        
        # Q3: Handling disagreements
        (3, "Talk immediately", 4),
        (3, "Cool down first", 3),
        (3, "Seek compromise", 2),
        (3, "Expect apology from the partner", 1),

        # Q4: listening quality
        (4, "Listen carefully and respond supportively", 4),
        (4, "Listen but give only practical advice", 3),
        (4, "Change the topic to lighten the mood", 2),
        (4, "Feel uncomfortable and avoid detailed discussion", 1),

        # Q5: Clarification behavior
        (5, "Clarify with patiently", 4),
        (5, "Repeat the same thing more firmly", 3),
        (5, "Get frustrated and stop explaining", 2),
        (5, "Let them assume what they want", 1),

        # Q6: Decision-making communication
        (6, "Discuss openly until both agree", 4),
        (6, "State your opinion and expect acceptance", 3),
        (6, "Let the partner decide to avoid arguments", 2),
        (6, "Avoid such discussions", 1),
        
        # Q7: This checks emotional safety, loyalty, and security in relationship.
        (7, "Let it go as heat-of-the-moment words", 4),
        (7, "Listen as there maybe a valid concern beneath the anger", 3),
        (7, "Consider it a low blow and demand an apology", 2),
        (7, "Defend your family immediately", 1),
        
        # Q8: Tests independence vs insecurity in relationship.
        (8, "Encourage it assuming individual time is healthy", 4),
        (8, "Prefer we travel and socialize mainly as a couple", 3),
        (8, "Expect the same freedom for yourself in return", 2),
        (8, "Feel uneasy and not allow", 1),

        # Q9: Transparency vs personal privacy
        (9, "They may be planning a surprise", 4),
        (9, "Concerned, but would ask for an explanation", 3),
        (9, "It's their privacy — no issue", 2),
        (9, "Suspicious — transparency is important", 1),

        # Q10: Boundary trust & honesty expectation
        (10, "Ignore", 4),
        (10, "Tell you immediately and ask for the next move", 3),
        (10, "Respond politely but keep distance", 2),
        (10, "Handle it discreetly without telling you", 1),
        
        # Q11: Money personality & spending discipline
        (11, "Balanced spender", 4),
        (11, "I let the partner manage", 3),
        (11, "Strict saver", 2),
        (11, "Spontaneous spender", 1),
        
        # Q12: Financial boundaries with extended family
        (12, "Always help family when needed", 4),
        (12, "Discuss and agree as a couple first", 3),
        (12, "Help only in emergencies", 2),
        (12, "Each person handles their own family", 1),

        # Q13:Financial self-esteem & power dynamics
        (13, "Proud and supportive", 4),
        (13, "Motivated to match them", 3),
        (13, "Relieved as financial pressure reduces", 2),
        (13, "Jealousy", 1),

        # Q14:Financial risk attitude & decision style
        (14, "Split funds and invest in both", 4),
        (14, "Go with the more knowledgeable partner's choice", 3),
        (14, "Choose the safer, more stable option", 2),
        (14, "Wait until you agree on one path", 1),
        
        # Q15: Physical-emotional closeness preference
        (15, "Frequent & important", 4),
        (15, "Quality over frequency", 3),
        (15, "Should be natural", 2),
        (15, "Adaptable to moods", 1),
        
        # Q16: Supportive vs reactive intimacy behavior
        (16, "Be patient and focus on emotional connection", 4),
        (16, "Discuss concerns gently to find solutions", 3),
        (16, "Seek ways to help reduce their stress first", 2),
        (16, "Feel rejected and address it directly", 1),

        # Q17: Openness to exploration
        (17, "Very important as keeping things exciting matters", 4),
        (17, "Only if both are comfortable", 3),
        (17, "Depends on mood and phase of life", 2),
        (17, "Not Intrested", 1),

        # Q18: Attachment through physical touch
        (18, "Very important as it keeps the connection alive daily", 4),
        (18, "It's main way of feeling secure.", 3),
        (18, "Nice when it happens naturally", 2),
        (18, "Feels irritated", 1),
        
        # Q19: In-law involvement tolerance
        (19, "Seek opinion but decision depends on the couple", 4),
        (19, "They should be involved in decisions", 3),
        (19, "Occasional contact only", 2),
        (19, "They should not be involved either in seeking opinion or decisons", 1),
        
        # Q20: family relationships
        (20, "Find an alternative like a home nearby", 4),
        (20, "Fulfill your parents wish as family comes first", 3),
        (20, "Convince your parents to live on their own", 2),
        (20, "Disagree", 1),

        # Q21: living location alignment
        (21, "Completely agree on where to live", 4),
        (21, "Mostly agree on location", 3),
        (21, "Some disagreement on location", 2),
        (21, "Major disagreement on where to live", 1),
        
        # Q22: cultural/religious values
        (22, "Nearly identical values", 4),
        (22, "Similar values with minor differences", 3),
        (22, "Quite different values causing issues", 2),
        (22, "Completely opposite values", 1),

        # Q23: support for goals
        (23, "Emotional partnership & love", 4),
        (23, "Building a family", 3),
        (23, "Practical & financial stability", 2),
        (23, "Personal & spiritual growth", 1),
        
        # Q24: Adjustment & compromise mindset
        (24, "Agree because it makes them happy", 4),
        (24, "Suggest alternative,if dosent works then compromise", 3),
        (24, "Let them have it as their responsibility", 2),
        (24, "Say no", 1),

        # Q25: Long-term growth philosophy
        (25, "Staying happy all the time", 4),
        (25, "Making good life decisions", 3),
        (25, "Raising children in good way", 2),
        (25, "Growing as individuals", 1),

        # Q26: Negotiation & mutual adaptability
        (26, "Find a shared destination", 4),
        (26, "Convince other partner to your desired place", 3),
        (26, "Alternate choices yearly", 2),
        (26, "Take two separate trips", 1),
        
        # Q27: Long-term family responsibility
        (27, "Definitely want kids", 4),
        (27, "Open to kids later", 3),
        (27, "Depends on partner", 2),
        (27, "Do not want kids", 1),
        
        # Q28: Career vs relationship priority
        (28, "Yes, only if partner agrees", 4),
        (28, "Discuss, but final say to job holder", 3),
        (28, "Only if works for both", 2),
        (28, "Prefer not to relocate", 1),

        # Q29: Responsibility sharing
        (29, "One manages, one helps", 4),
        (29, "Split by time(one having more ample time)", 3),
        (29, "Outsource to avoid conflict", 2),
        (29, "Split 50/50", 1),

        # Q30: Caregiving dedication
        (30, "Automatically handle all chores and care", 4),
        (30, "Nurse them intensely", 3),
        (30, "Show sympathy but u keep their works to them", 2),
        (30, "Expect them to ask for what they nee", 1),
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
