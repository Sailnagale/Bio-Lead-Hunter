def calculate_propensity_score(lead_row):
    """
    Calculates a score (0-100) based on weighted signals.
    """
    score = 0
    
  
    if lead_row.get('Has_Recent_Paper'):
        score += 40
        

    target_roles = ['toxicology', 'safety', 'hepatic', 'preclinical', 'vitro', '3d']
    title = str(lead_row.get('Title', '')).lower()

    if any(role in title for role in target_roles):
        score += 30

    if lead_row.get('Recent_Funding'):
        score += 20

    hubs = ['cambridge', 'boston', 'san francisco', 'bay area', 'basel', 'london', 'oxford']
    loc = str(lead_row.get('Location', '')).lower()
    
    if any(hub in loc for hub in hubs):
        score += 10
        
 
    return min(score, 100)