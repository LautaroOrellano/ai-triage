import os
import google.generativeai as genai

def generate_ai_response(issue_title, issue_body, bot_name, lang_code="en"):
    """
    Generates a response using Google Gemini AI if the API key is available.
    """
    api_key = os.getenv("AI_API_KEY")
    
    # Simple fallback translation for the mock response
    if not api_key:
        if lang_code == "es":
            return f"""
🤖 **Análisis de Asistente**:
He analizado el título y parece que tu problema trata sobre: *"{issue_title}"*.

Como todavía no has configurado una `AI_API_KEY`, no puedo darte una solución técnica exacta, pero mi lógica interna sugiere:
1. Revisa si hay errores similares en la documentación.
2. Asegúrate de que el entorno sea el correcto.

_(Configura el secreto `AI_API_KEY` con una key de Google Gemini para obtener respuestas inteligentes reales)_
"""
        else:
            return f"""
🤖 **Assistant Analysis**:
I've analyzed the title and it seems your problem is about: *"{issue_title}"*.

Since you haven't configured an `AI_API_KEY` yet, I cannot provide an exact technical solution, but my internal logic suggests:
1. Check if there are similar errors in the documentation.
2. Ensure the environment is correct.

_(Configure the `AI_API_KEY` secret with a Google Gemini key to get real smart responses)_
"""
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        language_name = "Spanish" if lang_code == "es" else "English"
        
        prompt = f"""
        You are an open source maintainer assistant named {bot_name}.
        Your goal is to help resolve this GitHub issue concisely and professionally.
        
        Issue Title: {issue_title}
        Issue Body: {issue_body}
        
        Instructions:
        1. Respond in {language_name}.
        2. If information seems missing (like logs or code), ask for it politely.
        3. Provide a possible cause of the problem and a suggest solution if possible.
        4. Be brief and direct.
        
        Response:
        """
        
        response = model.generate_content(prompt)
        return f"\n🤖 **AI Analysis ({bot_name})**:\n{response.text}\n"

    except Exception as e:
        error_msg = "No pude generar una respuesta" if lang_code == "es" else "Could not generate a response"
        return f"\n⚠️ **AI Error**: {error_msg}. ({str(e)})\n"