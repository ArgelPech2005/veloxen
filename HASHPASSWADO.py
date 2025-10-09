from werkzeug.security import generate_password_hash, check_password_hash

hashed_password = generate_password_hash("nando")
print(hashed_password)  