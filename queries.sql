-- Sample SQL Queries for Testing and Analysis

-- 1. View all questions with their options
SELECT 
    q.id,
    q.question_text,
    q.domain,
    o.option_text,
    o.weight
FROM questions q
JOIN options o ON q.id = o.question_id
ORDER BY q.id, o.weight DESC;

-- 2. Get all pair links and their completion status
SELECT 
    id,
    link_token,
    relationship_status,
    created_at,
    CASE WHEN is_complete = 1 THEN 'Complete' ELSE 'Pending' END as status
FROM pair_links
ORDER BY created_at DESC;

-- 3. View responses for a specific pair
SELECT 
    r.user_number,
    q.question_text,
    o.option_text,
    o.weight,
    q.domain
FROM responses r
JOIN questions q ON r.question_id = q.id
JOIN options o ON r.option_id = o.id
WHERE r.pair_id = 1  -- Change to specific pair_id
ORDER BY r.user_number, q.id;

-- 4. Calculate domain scores for a pair
SELECT 
    r.user_number,
    q.domain,
    SUM(o.weight) as domain_score,
    COUNT(*) as questions_answered
FROM responses r
JOIN questions q ON r.question_id = q.id
JOIN options o ON r.option_id = o.id
WHERE r.pair_id = 1  -- Change to specific pair_id
GROUP BY r.user_number, q.domain
ORDER BY r.user_number, q.domain;

-- 5. Compare both users' scores side by side
SELECT 
    q.domain,
    MAX(CASE WHEN r.user_number = 1 THEN o.weight END) as user1_score,
    MAX(CASE WHEN r.user_number = 2 THEN o.weight END) as user2_score,
    ABS(MAX(CASE WHEN r.user_number = 1 THEN o.weight END) - 
        MAX(CASE WHEN r.user_number = 2 THEN o.weight END)) as difference
FROM responses r
JOIN questions q ON r.question_id = q.id
JOIN options o ON r.option_id = o.id
WHERE r.pair_id = 1  -- Change to specific pair_id
GROUP BY q.domain, r.question_id
ORDER BY difference DESC;

-- 6. Get all results with predictions
SELECT 
    r.id,
    pl.relationship_status,
    r.prediction_label,
    r.probability_score,
    r.explanation,
    r.predicted_at
FROM results r
JOIN pair_links pl ON r.pair_id = pl.id
ORDER BY r.predicted_at DESC;

-- 7. Statistics: Count assessments by status
SELECT 
    relationship_status,
    COUNT(*) as total_assessments,
    SUM(CASE WHEN is_complete = 1 THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN is_complete = 0 THEN 1 ELSE 0 END) as pending
FROM pair_links
GROUP BY relationship_status;

-- 8. Find pairs with highest compatibility/lowest risk
SELECT 
    pl.id,
    pl.relationship_status,
    r.prediction_label,
    r.probability_score,
    r.predicted_at
FROM results r
JOIN pair_links pl ON r.pair_id = pl.id
ORDER BY 
    CASE 
        WHEN pl.relationship_status = 'unmarried' THEN r.probability_score
        ELSE -r.probability_score
    END DESC
LIMIT 10;

-- 9. Domain-wise average scores across all assessments
SELECT 
    q.domain,
    AVG(o.weight) as avg_score,
    MIN(o.weight) as min_score,
    MAX(o.weight) as max_score
FROM responses r
JOIN questions q ON r.question_id = q.id
JOIN options o ON r.option_id = o.id
GROUP BY q.domain
ORDER BY avg_score DESC;

-- 10. Response time analysis (how long users take)
SELECT 
    pair_id,
    user_number,
    MIN(response_time) as first_response,
    MAX(response_time) as last_response,
    COUNT(*) as total_questions
FROM responses
GROUP BY pair_id, user_number;

-- 11. Most problematic domains (lowest average scores)
SELECT 
    q.domain,
    AVG(o.weight) as avg_score,
    COUNT(DISTINCT r.pair_id) as num_couples
FROM responses r
JOIN questions q ON r.question_id = q.id
JOIN options o ON r.option_id = o.id
GROUP BY q.domain
HAVING avg_score < 2.5
ORDER BY avg_score ASC;

-- 12. Delete old incomplete pairs (cleanup)
-- Uncomment to use - deletes pairs older than 7 days that weren't completed
/*
DELETE FROM pair_links 
WHERE is_complete = 0 
AND datetime(created_at) < datetime('now', '-7 days');
*/

-- 13. Export all data for a specific pair (for reporting)
SELECT 
    'Pair Information' as section,
    pl.link_token as data,
    pl.relationship_status as detail,
    pl.created_at as timestamp
FROM pair_links pl
WHERE pl.id = 1
UNION ALL
SELECT 
    'User ' || r.user_number || ' Response' as section,
    q.question_text as data,
    o.option_text as detail,
    r.response_time as timestamp
FROM responses r
JOIN questions q ON r.question_id = q.id
JOIN options o ON r.option_id = o.id
WHERE r.pair_id = 1
UNION ALL
SELECT 
    'Prediction Result' as section,
    r.prediction_label as data,
    CAST(r.probability_score as TEXT) || '%' as detail,
    r.predicted_at as timestamp
FROM results r
WHERE r.pair_id = 1;

-- 14. Check database integrity
SELECT 
    'Total Questions' as metric,
    COUNT(*) as value
FROM questions
UNION ALL
SELECT 
    'Total Options',
    COUNT(*)
FROM options
UNION ALL
SELECT 
    'Total Pairs Created',
    COUNT(*)
FROM pair_links
UNION ALL
SELECT 
    'Completed Assessments',
    COUNT(*)
FROM pair_links
WHERE is_complete = 1
UNION ALL
SELECT 
    'Total Responses',
    COUNT(*)
FROM responses
UNION ALL
SELECT 
    'Total Predictions',
    COUNT(*)
FROM results;

-- 15. Find incomplete pairs (for follow-up reminders)
SELECT 
    pl.id,
    pl.link_token,
    pl.relationship_status,
    pl.created_at,
    julianday('now') - julianday(pl.created_at) as days_old
FROM pair_links pl
WHERE pl.is_complete = 0
ORDER BY pl.created_at DESC;
