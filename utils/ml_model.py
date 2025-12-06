import numpy as np
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

def create_features(user1_scores, user2_scores):
    """
    Create feature vector from both users' domain scores
    
    Features include:
    - Individual domain scores for both users
    - Difference between partners in each domain
    - Total scores for each user
    - Similarity score (inverse of total difference)
    """
    domains = ['communication', 'trust', 'finance', 'intimacy', 
               'family', 'personal_growth', 'commitment']
    
    features = []
    
    # Individual scores
    for domain in domains:
        features.append(user1_scores.get(domain, 0))
    
    for domain in domains:
        features.append(user2_scores.get(domain, 0))
    
    # Differences (absolute)
    for domain in domains:
        diff = abs(user1_scores.get(domain, 0) - user2_scores.get(domain, 0))
        features.append(diff)
    
    # Total scores
    total_user1 = sum(user1_scores.values())
    total_user2 = sum(user2_scores.values())
    features.append(total_user1)
    features.append(total_user2)
    
    # Total difference (dissimilarity)
    total_diff = sum(abs(user1_scores.get(d, 0) - user2_scores.get(d, 0)) for d in domains)
    features.append(total_diff)
    
    # Average score
    avg_score = (total_user1 + total_user2) / 2
    features.append(avg_score)
    
    return np.array(features).reshape(1, -1)

def train_model():
    """
    Train a machine learning model
    In production, this would use real data
    For now, we'll create a simple rule-based predictor
    """
    # This is a placeholder - in real scenario, you'd load training data
    # and train a proper model
    pass

def load_model():
    """
    Load trained model from disk
    Returns None if model doesn't exist (we'll use rule-based prediction)
    """
    model_path = 'models/compatibility_model.pkl'
    if os.path.exists(model_path):
        with open(model_path, 'rb') as f:
            return pickle.load(f)
    return None

def predict_compatibility(user1_scores, user2_scores, relationship_status):
    """
    Predict compatibility or divorce risk based on responses
    
    Parameters:
    - user1_scores: dict of domain -> score for user 1
    - user2_scores: dict of domain -> score for user 2
    - relationship_status: 'married' or 'unmarried'
    
    Returns:
    - prediction: string label
    - probability: float (0-1)
    - explanation: string explanation
    """
    
    domains = ['communication', 'trust', 'finance', 'intimacy', 
               'family', 'personal_growth', 'commitment']
    
    # Calculate metrics
    total_user1 = sum(user1_scores.values())
    total_user2 = sum(user2_scores.values())
    avg_score = (total_user1 + total_user2) / 2
    max_possible = len(domains) * 4 * 2  # max score per domain * 2 users
    
    # Calculate similarity (lower difference = higher compatibility)
    total_diff = sum(abs(user1_scores.get(d, 0) - user2_scores.get(d, 0)) for d in domains)
    max_diff = len(domains) * 4
    similarity = 1 - (total_diff / max_diff)
    
    # Combined score (weighted average of absolute scores and similarity)
    combined_score = (avg_score / (len(domains) * 8)) * 0.6 + similarity * 0.4
    
    # Identify problem areas (low scores or big differences)
    problem_domains = []
    for domain in domains:
        avg_domain = (user1_scores.get(domain, 0) + user2_scores.get(domain, 0)) / 2
        diff = abs(user1_scores.get(domain, 0) - user2_scores.get(domain, 0))
        
        if avg_domain < 2.5 or diff > 2:
            problem_domains.append(domain)
    
    # Generate prediction based on relationship status
    if relationship_status == 'unmarried':
        # Compatibility prediction for unmarried couples
        if combined_score >= 0.75:
            prediction = "Excellent Compatibility"
            probability = combined_score
            explanation = f"You both show strong alignment across {len(domains) - len(problem_domains)} out of {len(domains)} key relationship domains. "
            if problem_domains:
                explanation += f"Consider discussing: {', '.join(problem_domains)} for even better harmony."
            else:
                explanation += "Keep nurturing your connection!"
        elif combined_score >= 0.60:
            prediction = "Good Compatibility"
            probability = combined_score
            explanation = f"You have a solid foundation with good alignment in most areas. "
            if problem_domains:
                explanation += f"Work together on: {', '.join(problem_domains)} to strengthen your relationship."
        elif combined_score >= 0.45:
            prediction = "Moderate Compatibility"
            probability = combined_score
            explanation = f"Your relationship has potential, but requires effort. "
            explanation += f"Focus on improving: {', '.join(problem_domains[:3])} through open communication and compromise."
        else:
            prediction = "Low Compatibility"
            probability = combined_score
            explanation = f"Significant differences detected in: {', '.join(problem_domains)}. "
            explanation += "Consider couples counseling or have honest conversations about long-term compatibility."
    
    else:  # married
        # Divorce risk prediction for married couples
        if combined_score >= 0.70:
            prediction = "Low Divorce Risk"
            probability = 1 - combined_score  # inverse for risk
            explanation = f"Your marriage shows strong health across key areas. "
            if problem_domains:
                explanation += f"Continue working on: {', '.join(problem_domains)} to maintain this positive trajectory."
            else:
                explanation += "Keep investing in your relationship!"
        elif combined_score >= 0.55:
            prediction = "Moderate Divorce Risk"
            probability = 1 - combined_score
            explanation = f"Your marriage has areas of concern. "
            explanation += f"Priority areas to address: {', '.join(problem_domains[:3])}. Consider marriage counseling to strengthen your bond."
        elif combined_score >= 0.40:
            prediction = "High Divorce Risk"
            probability = 1 - combined_score
            explanation = f"Your marriage shows significant stress in: {', '.join(problem_domains)}. "
            explanation += "Professional intervention is strongly recommended. Many marriages can be saved with proper support."
        else:
            prediction = "Critical Divorce Risk"
            probability = 1 - combined_score
            explanation = f"Your marriage faces serious challenges across multiple domains: {', '.join(problem_domains)}. "
            explanation += "Immediate professional help is crucial. Both partners must be committed to making changes."
    
    # Add specific domain insights
    strength_domains = [d for d in domains if d not in problem_domains]
    if strength_domains:
        explanation += f"\n\nStrengths: {', '.join(strength_domains)}."
    
    return prediction, round(probability * 100, 1), explanation

def get_recommendation(prediction, relationship_status):
    """Generate actionable recommendations based on prediction"""
    recommendations = []
    
    if relationship_status == 'unmarried':
        if 'Excellent' in prediction:
            recommendations = [
                "Continue building on your strong foundation",
                "Discuss long-term goals and values regularly",
                "Consider pre-marital counseling to prepare for marriage"
            ]
        elif 'Good' in prediction:
            recommendations = [
                "Have deep conversations about identified concern areas",
                "Set aside quality time for each other weekly",
                "Consider couples workshops or relationship coaching"
            ]
        elif 'Moderate' in prediction:
            recommendations = [
                "Seek couples counseling before making long-term commitments",
                "Work on communication skills together",
                "Take time to understand each other's perspectives"
            ]
        else:
            recommendations = [
                "Have honest conversations about compatibility",
                "Consider whether this relationship meets both your needs",
                "Seek individual and couples therapy if moving forward"
            ]
    else:  # married
        if 'Low' in prediction:
            recommendations = [
                "Continue your positive relationship habits",
                "Schedule regular check-ins about your relationship",
                "Don't take your strong bond for granted"
            ]
        elif 'Moderate' in prediction:
            recommendations = [
                "Start marriage counseling to address concerns",
                "Commit to working on specific problem areas together",
                "Increase quality time and positive interactions"
            ]
        elif 'High' in prediction or 'Critical' in prediction:
            recommendations = [
                "Seek immediate professional marriage counseling",
                "Both partners must commit to making changes",
                "Consider intensive therapy or marriage retreat programs",
                "Focus on rebuilding trust and communication"
            ]
    
    return recommendations
