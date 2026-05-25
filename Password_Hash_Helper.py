
import streamlit_authenticator as stauth

plain_password = input("Enter password to hash: ")
hashed_password = stauth.Hasher().hash(plain_password)

print("\n✅ Hashed password:")
print(hashed_password)
print("\nCopy this hash and paste it into your credentials.yaml file.")


