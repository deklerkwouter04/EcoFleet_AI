
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# Load existing credentials.yaml
with open('credentials.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Loop through each user and hash their password
for username, details in config['credentials']['usernames'].items():
    plain_password = details['password']
    hashed_password = stauth.Hasher().hash(plain_password)
    config['credentials']['usernames'][username]['password'] = hashed_password

# Save updated credentials.yaml
with open('credentials.yaml', 'w') as file:
    yaml.dump(config, file)

print("✅ Passwords hashed and credentials.yaml updated successfully!")






