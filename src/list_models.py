import os
from google import genai

def main():
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        print("DEBUG_MODELS: No AI_API_KEY provided.")
        return
        
    client = genai.Client(api_key=api_key)
    try:
        print("DEBUG_MODELS: --- DISPONIBLES EN TU API KEY ---")
        for model in client.models.list():
            print(f"Nombre real para el código: '{model.name}' | Muestra: {model.display_name}")
    except Exception as e:
        print(f"DEBUG_MODELS: Error fetching models: {e}")

if __name__ == "__main__":
    main()
