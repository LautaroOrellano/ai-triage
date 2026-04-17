import os
from google import genai
from google.genai import types

def get_repo_context():
    """Reads the repository's README.md to provide real context to the AI."""
    workspace = os.getenv("GITHUB_WORKSPACE", ".")
    
    for possible_name in ["README.md", "readme.md", "README.txt", "Readme.md"]:
        path = os.path.join(workspace, possible_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    return content[:15000]
            except Exception as e:
                continue
                
    return ""

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
🤖 **Assistant Analysis**:
I've analyzed the title and it seems your problem is about: *"{issue_title}"*.

Since you haven't configured an `AI_API_KEY` yet, I cannot provide an exact technical solution, but my internal logic suggests:
1. Check if there are similar errors in the documentation.
2. Ensure the environment is correct.

_(Configure the `AI_API_KEY` secret with a Google Gemini key to get real smart responses)_
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
        
        repo_context = get_repo_context()
        context_block = ""
        if repo_context:
            context_block = f"\n\n--- OFFICIAL REPOSITORY DOCUMENTATION (README) ---\n{repo_context}\n----------------------------------------------------\nIMPORTANT: Use the documentation above as your absolute source of truth. If the user asks something covered in the README, quote it. If the documentation contradicts their assumed generic names (like 'ProjectA'), correct them gently using the real project name and config from the documentation above."
        
        if is_direct and user_comment:
            prompt = f"""
            You are an open source maintainer assistant named {bot_name}.
            A user has asked you a specific question or mentioned you in a GitHub issue thread.
            
            Context of the Issue:
            Title: {issue_title}
            Body: {issue_body}
            {context_block}
            
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
            {context_block}
            
            Instructions:
            1. Respond in {language_name}.
            2. If information seems missing (like logs or code), ask for it politely.
            3. Provide a possible cause of the problem and a suggest solution if possible.
            4. Be brief and direct.
            
            Response:
            """
        
        models_to_try = [
            # Priority 1: 500 free daily calls of Gemini 3.1 Flash Lite Preview
            'gemini-3.1-flash-lite-preview',
            # Priority 2: 1500 free daily calls of Gemini 2.0 Flash
            'gemini-2.0-flash',
            # Priority 3: 1500 free daily calls of Gemini 2.0 Flash Lite
            'gemini-2.0-flash-lite',
            # Priority 4: Fallback
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
                
        # If it reached here, all models failed
        if not is_direct:
            # On cron sweep tasks, if AI fails, abort silently to avoid spamming errors on old issues
            return None
            
        error_msg = "No pude generar una respuesta" if lang_code == "es" else "Could not generate a response"
        return f"\n⚠️ **AI Error**: {error_msg}. ({str(last_error)})\n"

    except Exception as e:
        error_msg = "No pude generar una respuesta" if lang_code == "es" else "Could not generate a response"
        return f"\n⚠️ **AI Error**: {error_msg}. ({str(e)})\n"

def generate_issue_label(title, body):
    """
    Analyzes an issue's title and body and returns a list of category labels.
    Used for silent auto-labeling without spamming comments.
    """
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        return None
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
Analyze the following GitHub issue and categorize it by selecting UP TO 5 applicable labels from the following list:
- bug
- enhancement
- question
- help wanted
- documentation
- good first issue

Issue Title: {title}
Issue Body: {body}

Return ONLY a comma-separated list of the chosen labels (e.g. "bug, documentation"). Do not include any extra text, markdown, or punctuation.
"""
    models_to_try = [
        'gemini-3.1-flash-lite-preview',
        'gemini-2.0-flash',
        'gemini-2.0-flash-lite',
        'gemini-flash-latest'
    ]
    
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,  # Low temperature
                )
            )
            
            
            raw_response = response.text.strip().lower()
            valid_labels = ["bug", "enhancement", "question", "help wanted", "documentation", "good first issue"]
            
            chosen_labels = []
            for valid in valid_labels:
                if valid in raw_response:
                    chosen_labels.append(valid)
                    
            if chosen_labels:
                return chosen_labels
            return None
            
        except Exception as e:
            continue
            
    return None

def detect_duplicate_issue(new_title, new_body, recent_issues):
    """
    Uses Gemini to compare a new issue against recent ones to find potential duplicates.
    Returns the issue number if a duplicate is found, otherwise None.
    """
    api_key = os.getenv("AI_API_KEY")
    if not api_key or not recent_issues:
        return None
        
    client = genai.Client(api_key=api_key)
    
    issues_list_str = "\n".join([f"- #{i['number']}: {i['title']}" for i in recent_issues])
    
    prompt = f"""
You are a GitHub maintainer assistant. Your task is to check if the new issue below is a duplicate of any of the recently opened issues.

--- NEW ISSUE ---
Title: {new_title}
Body: {new_body}

--- RECENT ISSUES LIST ---
{issues_list_str}

Instructions:
1. Compare the new issue's meaning and goal against the recent issues list.
2. If it is a clear duplicate, return ONLY the issue number (e.g., "123").
3. If it's NOT a duplicate or you are unsure, return exactly: "NONE".

Response:
"""
    models_to_try = ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-flash-latest']
    
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1)
            )
            resp_text = response.text.strip().upper()
            if "NONE" in resp_text:
                return None
            
            # Extract number from response
            import re
            match = re.search(r'\d+', resp_text)
            if match:
                return int(match.group())
            return None
        except Exception:
            continue
            
    return None
