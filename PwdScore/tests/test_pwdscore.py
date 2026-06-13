from pwdscore import score, check

def test_score_empty():
    assert score("") == 0

def test_score_length():
    # Only lowercase, length 5 = 5 * 4 + 15 = 35
    assert score("hello") == 35

def test_score_variety():
    # Length 8 (32) + lower (15) + upper (15) + digit (15) + special (15) = 92
    assert score("Hello12!") == 92

def test_score_max():
    # Length 20 (40) + all varieties (60) = 100
    assert score("VeryLongPassword123!@#") == 100

def test_check_weak():
    assert check("hi") == "Weak"
    assert check("hello") == "Weak"

def test_check_medium():
    # Length 8 (32) + lower (15) + upper (15) = 62
    assert check("HelloWorld") == "Medium"

def test_check_strong():
    assert check("Hello123World!") == "Strong"
