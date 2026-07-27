import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")

client = Groq(api_key=api_key)

response = client.chat.completions.create(
    model="llama-3.1-8b-instant",   # Groq supports LLaMA models
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Break down the task: Prepare a market analysis report for Q2"}
    ]
)

print(response.choices[0].message.content)
