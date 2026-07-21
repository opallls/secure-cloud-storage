import streamlit_authenticator as stauth

password = "SecurePass123"
hasher = stauth.Hasher()
hashed = hasher.hash(password)
print("Hash:", hashed)