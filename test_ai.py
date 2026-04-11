import os
from google import genai

def test():
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        print("No API KEY")
        return
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents="say hello"
        )
        print("Response:", response.text)
    except Exception as e:
        print("Error:", e)

test()
