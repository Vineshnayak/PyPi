import string

def score(password: str) -> int:
    """
    Calculate a password strength score from 0 to 100 based on its characteristics.

    The score is determined by:
    - Length: up to 40 points
    - Uppercase letters: 15 points
    - Lowercase letters: 15 points
    - Digits: 15 points
    - Special characters: 15 points

    Args:
        password: The password string to evaluate.

    Returns:
        An integer between 0 and 100 representing the strength score.
    """
    if not password:
        return 0

    score_val = 0
    length = len(password)

    # Length contribution (up to 40 points)
    # Give 4 points per character up to 10 characters
    score_val += min(length * 4, 40)

    # Variety contribution (up to 60 points)
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in string.punctuation for c in password)

    if has_lower:
        score_val += 15
    if has_upper:
        score_val += 15
    if has_digit:
        score_val += 15
    if has_special:
        score_val += 15

    return min(score_val, 100)

def check(password: str) -> str:
    """
    Check the password strength and return a category.

    Args:
        password: The password string to evaluate.

    Returns:
        'Weak' (score < 50), 'Medium' (score < 80), or 'Strong' (score >= 80).
    """
    s = score(password)
    if s < 50:
        return "Weak"
    elif s < 80:
        return "Medium"
    else:
        return "Strong"
