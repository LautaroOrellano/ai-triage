import os
import json
from github_client import GitHubClient
from utils import should_respond, was_mentioned, check_missing_info
from ai_handler import generate_ai_response

TOKEN = os.getenv("GITHUB_TOKEN")
DELAY = int(os.getenv("DELAY_MINUTES", "30"))
BOT_NAME = os.getenv("BOT_NAME", "helperbot")
EVENT_PATH = os.getenv("GITHUB_EVENT_PATH")
EVENT_NAME = os.getenv("GITHUB_EVENT_NAME")
LANGUAGE = os.getenv("LANGUAGE", "en").lower()
LABEL_NAME = "bot-responded"

client = GitHubClient(TOKEN)

LOCALIZATION = {
    "en": {
        "welcome": "👋 Hi! I'm **{bot_name}**",
        "mentioned": "You mentioned me! I'm here to help 🚀",
        "stale": "It looks like no one has responded yet ⏳",
        "tips_header": "💡 **Tips to get faster help:**",
        "missing_item": "- Please provide more {item}.",
        "guidance": "💬 Mention me with `@{bot_name}` if you need more direct guidance.",
        "items": {
            "logs": "code blocks or logs",
            "details": "detailed explanation",
            "description": "description of the issue"
        }
    },
    "es": {
        "welcome": "👋 ¡Hola! Soy **{bot_name}**",
        "mentioned": "¡Me has mencionado! Estoy aquí para ayudarte 🚀",
        "stale": "Parece que nadie ha respondido aún ⏳",
        "tips_header": "💡 **Consejos para obtener ayuda más rápido:**",
        "missing_item": "- Por favor, proporciona más {item}.",
        "guidance": "💬 Mencióname con `@{bot_name}` si necesitas ayuda más específica.",
        "items": {
            "logs": "bloques de código o registros (logs)",
            "details": "explicación detallada",
            "description": "descripción del problema"
        }
    }
}

def load_event():
    if not EVENT_PATH or not os.path.exists(EVENT_PATH):
        return {}
    with open(EVENT_PATH, "r") as f:
        return json.load(f)

def process_issue(issue_obj, trigger_text=None):
    """Core logic to decide if the bot should reply to a specific issue."""
    issue_number = issue_obj.number
    body = issue_obj.body or ""
    title = issue_obj.title
    
    # Text to check for mentions (can be the comment body or issue body)
    text_to_check = trigger_text if trigger_text else body

    # Trigger 1: Direct Mention (Prioritized)
    if was_mentioned(text_to_check, BOT_NAME):
        response = format_response(title, body, direct=True, user_comment=text_to_check)
        client.comment(issue_number, response)
        client.add_label(issue_number, LABEL_NAME)
        return

    # Trigger 2: Delay Check
    if client.has_label(issue_number, LABEL_NAME) or client.already_commented(issue_number):
        return

    comments = client.get_comments(issue_number)
    if should_respond(str(issue_obj.created_at), comments, DELAY):
        response = format_response(title, body)
        client.comment(issue_number, response)
        client.add_label(issue_number, LABEL_NAME)

def format_response(title, body, direct=False, user_comment=None):
    lang_code = LANGUAGE if LANGUAGE in LOCALIZATION else "en"
    strings = LOCALIZATION[lang_code]
    
    missing = check_missing_info(body)
    ai_resp = generate_ai_response(title, body, BOT_NAME, lang_code, user_comment, direct)
    
    # If direct mention and AI replied correctly, skip generic boilerplate
    if direct and ai_resp and "⚠️" not in ai_resp and "Análisis de Asistente" not in ai_resp and "Assistant Analysis" not in ai_resp:
        return ai_resp
        
    msg = strings["welcome"].format(bot_name=BOT_NAME) + "\n\n"
    
    if direct:
        msg += strings["mentioned"] + "\n\n"
    else:
        msg += strings["stale"] + "\n\n"

    # Only show missing info generic tips on initial sweep, not on conversational mentions
    if missing and not direct:
        msg += strings["tips_header"] + "\n"
        for item_key in missing:
            localized_item = strings["items"].get(item_key, item_key)
            msg += strings["missing_item"].format(item=localized_item) + "\n"
        msg += "\n"

    if ai_resp:
        msg += f"{ai_resp}\n"
    else:
        if not direct:
            msg += strings["guidance"].format(bot_name=BOT_NAME) + "\n"
        
    return msg

def main():
    event = load_event()

    if EVENT_NAME == "issues" or EVENT_NAME == "issue_comment":
        if "issue" in event:
            issue_number = event["issue"]["number"]
            issue_obj = client.repo.get_issue(issue_number)
            
            trigger_text = None
            if "comment" in event:
                trigger_text = event["comment"]["body"]
            
            process_issue(issue_obj, trigger_text=trigger_text)
    
    elif EVENT_NAME == "schedule" or not EVENT_NAME:
        issues = client.get_open_issues()
        for issue in issues:
            process_issue(issue)

if __name__ == "__main__":
    main()