import hashlib

salt = "05052025"

def hash_password(password):
    password_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return password_hash

def verify_password(stored_password, provided_password):
    password_hash = hashlib.sha256((provided_password + salt).encode('utf-8')).hexdigest()
    return password_hash == stored_password
