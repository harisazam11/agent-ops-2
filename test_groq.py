import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv(".env")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

try:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": "Say hello in one word"}],
    )
    result = response.choices[0].message.content
    print(f"llama-3.1-8b-instant: OK -> {result.strip()}")
except Exception as e:
    print(f"llama-3.1-8b-instant: FAIL -> {e}")
