import os
import sys
# import django  <-- Removed to avoid errors if env not active
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

print(f"Testing Groq connection with API Key: {os.getenv('GROQ_API_KEY')[:10]}...")

from litellm import completion

try:
    print("Sending request to Groq (llama-3.1-8b-instant)...")
    response = completion(
        model="groq/llama-3.1-8b-instant", 
        messages=[{ "content": "Hello, just testing connectivity.","role": "user"}]
    )
    print("\n✅ SUCCESS!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
