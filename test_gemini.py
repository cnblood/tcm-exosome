import os
from google import genai
client = genai.Client(api_key=os.environ['GEMINI_API_KEY'].strip())
response = client.models.generate_content(model="gemini-2.0-flash-lite", contents="test")
print("OK:", response.text[:50])
