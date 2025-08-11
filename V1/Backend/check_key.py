# check_key.py

from config.config import config

print("--- Key Diagnostic Tool ---")
print("Attempting to load OPENAI_API_KEY from .env file...")

# Get the key from our config loader
api_key = config.get('OPENAI_API_KEY')

if api_key and len(api_key) > 10:
    print("\n✅ Success! The API key was found and loaded correctly.")
    # For security, we only show the beginning and end of the key
    print(f"   Key snippet: {api_key[:6]}...{api_key[-4:]}")
else:
    print("\n❌ Failure! The API key was not found or is invalid.")
    print("   Please proceed to the troubleshooting checklist below.")

print("--- End of Diagnostic ---")