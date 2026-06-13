from src.pwdscore import score, check

my_password = "pass127!"

print(f"Password: {my_password}")
print(f"Score: {score(my_password)}/100")
print(f"Strength: {check(my_password)}")
