import os
import google.generativeai as genai

def generate_ai_response(issue_title, issue_body, bot_name):
    """
    Generates a response using Google Gemini AI if the API key is available.
    """
    api_key = os.getenv("AI_API_KEY")
    
    if not api_key:
        return f"""
🤖 **Análisis de Asistente**:
He analizado el título y parece que tu problema trata sobre: *"{issue_title}"*.

Como todavía no has configurado una `AI_API_KEY`, no puedo darte una solución técnica exacta, pero mi lógica interna sugiere:
1. Revisa si hay errores similares en la documentación.
2. Asegúrate de que el entorno sea el correcto.

_(Configura el secreto `AI_API_KEY` con una key de Google Gemini para obtener respuestas inteligentes reales)_
"""
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Eres un asistente de mantenimiento de código abierto llamado {bot_name}.
        Tu objetivo es ayudar a resolver este issue de GitHub de forma concisa y profesional.
        
        Título del Issue: {issue_title}
        Cuerpo del Issue: {issue_body}
        
        Instrucciones:
        1. Responde en Español.
        2. Si parece que falta información (como logs o código), pídela amablemente.
        3. Proporciona una posible causa del problema y una sugerencia de solución si es posible.
        4. Sé breve y directo.
        
        Respuesta:
        """
        
        response = model.generate_content(prompt)
        return f"\n🤖 **Análisis de IA ({bot_name})**:\n{response.text}\n"

    except Exception as e:
        return f"\n⚠️ **Error de IA**: No pude generar una respuesta inteligente en este momento. ({str(e)})\n"