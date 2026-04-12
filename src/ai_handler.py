import os
from google import genai

def generate_ai_response(issue_title, issue_body, bot_name, lang_code="en", user_comment=None, is_direct=False):
    """
    Generates a response using Google Gemini AI if the API key is available.
    """
    api_key = os.getenv("AI_API_KEY")
    
    # Simple fallback translation for the mock response
    if not api_key:
        if lang_code == "es":
            if is_direct:
                return f"🤖 **Asistente**: He leído tu comentario. Pero sin `AI_API_KEY` configurada, no puedo responder preguntas complejas."
            return f"""
🤖 **Análisis de Asistente**:
He analizado el título y parece que tu problema trata sobre: *"{issue_title}"*.

Como todavía no has configurado una `AI_API_KEY`, no puedo darte una solución técnica exacta, pero mi lógica interna sugiere:
1. Revisa si hay errores similares en la documentación.
2. Asegúrate de que el entorno sea el correcto.

_(Configura el secreto `AI_API_KEY` con una key de Google Gemini para obtener respuestas inteligentes reales)_
"""
        else:
            if is_direct:
                return f"🤖 **Assistant**: I've read your comment. But without an `AI_API_KEY` configured, I cannot answer complex questions."
            return f"""
🤖 **Assistant Analysis**:
I've analyzed the title and it seems your problem is about: *"{issue_title}"*.

Since you haven't configured an `AI_API_KEY` yet, I cannot provide an exact technical solution, but my internal logic suggests:
1. Check if there are similar errors in the documentation.
2. Ensure the environment is correct.

_(Configure the `AI_API_KEY` secret with a Google Gemini key to get real smart responses)_
"""
    
    try:
        # Create the new genai Client
        client = genai.Client(api_key=api_key)
        
        language_name = "Spanish" if lang_code == "es" else "English"
        
        if is_direct and user_comment:
            prompt = f"""
            You are an open source maintainer assistant named {bot_name}.
            A user has asked you a specific question or mentioned you in a GitHub issue thread.
            
            Context of the Issue:
            Title: {issue_title}
            Body: {issue_body}
            
            User's Comment to you:
            "{user_comment}"
            
            Instructions:
            1. Respond in {language_name}.
            2. Address the user's specific comment/question directly.
            3. Be conversational, helpful, and concise. Don't act overly robotic.
            
            Response:
            """
        else:
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
        
        models_to_try = [
            # Prioridad 1: 500 gratuitas de Gemini 3.1 Flash Lite Preview
            'gemini-3.1-flash-lite-preview',
            # Prioridad 2: 1500 gratuitas de Gemini 2.0 Flash
            'gemini-2.0-flash',
            # Prioridad 3: 1500 gratuitas de Gemini 2.0 Flash Lite
            'gemini-2.0-flash-lite',
            # Prioridad 4: Respaldo extra
            'gemini-flash-latest'
        ]
        
        last_error = None
        for model_name in models_to_try:
            try:
                # Call the API using the new Client structure
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                icon = "💬" if is_direct else "🤖"
                title_block = "" if is_direct else f"**AI Analysis ({bot_name})**:\n"
                return f"\n{icon} {title_block}{response.text}\n"
            except Exception as e:
                last_error = e
                continue
                
        # Si llegó aquí es porque falló todo
        if not is_direct:
            # En sweep (cron), si falla la IA, mejor abortar silenciosamente para no spamear errores a todos los issues viejos
            return None
            
        error_msg = "No pude generar una respuesta" if lang_code == "es" else "Could not generate a response"
        return f"\n⚠️ **AI Error**: {error_msg}. ({str(last_error)})\n"

    except Exception as e:
        error_msg = "No pude generar una respuesta" if lang_code == "es" else "Could not generate a response"
        return f"\n⚠️ **AI Error**: {error_msg}. ({str(e)})\n"

def generate_issue_label(title, body):
    """
    Analyzes an issue's title and body and returns a single category label.
    Used for silent auto-labeling without spamming comments.
    """
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        return None
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
Analyze the following GitHub issue and categorize it into EXACTLY ONE of these labels:
- bug
- enhancement
- question
- help wanted

Issue Title: {title}
Issue Body: {body}

Return ONLY the label name in lowercase, with no extra text, markdown, or punctuation.
"""
    models_to_try = [
        'gemini-3.1-flash-lite-preview',
        'gemini-2.0-flash',
        'gemini-2.0-flash-lite',
        'gemini-flash-latest'
    ]
    
    for model_name in models_to_try:
        try:
            print(f"DEBUG_PRINT_LOCAL: Intentando modelo {model_name} para la etiqueta...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,  # Low temperature for strict classification
                )
            )
            
            # Print de la respuesta cruda de Gemini para depurar
            print(f"DEBUG_PRINT_LOCAL: Gemini respondió en crudo: {repr(response.text)}")
            
            label = response.text.strip().lower()
            valid_labels = ["bug", "enhancement", "question", "help wanted"]
            
            for valid in valid_labels:
                if valid in label:
                    return valid
            print(f"DEBUG_PRINT_LOCAL: El texto no contenía ninguna de las etiquetas válidas.")
            return None
            
        except Exception as e:
            print(f"DEBUG_PRINT_LOCAL: El modelo {model_name} falló con error: {str(e)}")
            continue
            
    print("DEBUG_PRINT_LOCAL: Se intentaron todos los modelos y fallaron todos.")
    return None