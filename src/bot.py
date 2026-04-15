import os
import json
from github_client import GitHubClient
from utils import should_respond, was_mentioned, check_missing_info, is_stale_zombie
from ai_handler import generate_ai_response, generate_issue_label, detect_duplicate_issue

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
        },
        "duplicate": "🛡️ **Duplicate Detected!** It seems this topic is already being discussed in #{duplicate_number}.",
        "zombie_close": "😴 **Auto-Closing due to inactivity.** This issue has been inactive for more than 2 years. Please open a new issue if this is still relevant."
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
        },
        "duplicate": "🛡️ **¡Duplicado Detectado!** Parece que este tema ya se está discutiendo en el issue #{duplicate_number}.",
        "zombie_close": "😴 **Cierre automático por inactividad.** Este issue ha estado inactivo por más de 2 años. Por favor, abre uno nuevo si el problema persiste."
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

    # --- ZOMBIE AUTO-CLOSE (v1.3.0 Feature) ---
    if EVENT_NAME == "schedule" or not EVENT_NAME:
        if is_stale_zombie(issue_obj.updated_at):
            lang_code = LANGUAGE if LANGUAGE in LOCALIZATION else "en"
            client.comment(issue_number, LOCALIZATION[lang_code]["zombie_close"])
            client.close_issue(issue_number)
            return
    # ------------------------------------------

    # Trigger 1: Direct Mention (Prioritized)
    # Never process mentions during a scheduled sweep
    if EVENT_NAME and EVENT_NAME != "schedule" and was_mentioned(text_to_check, BOT_NAME):
        response = format_response(title, body, direct=True, user_comment=text_to_check)
        if response:
            client.comment(issue_number, response)
            client.add_label(issue_number, LABEL_NAME)
        return

    # Trigger 2: Delay Check
    if client.has_label(issue_number, LABEL_NAME):
        return
        
    if client.already_commented(issue_number):
        return

    comments = client.get_comments(issue_number)
    if should_respond(str(issue_obj.created_at), comments, DELAY):
        response = format_response(title, body)
        if response:
            client.comment(issue_number, response)
            client.add_label(issue_number, LABEL_NAME)

def format_response(title, body, direct=False, user_comment=None):
    lang_code = LANGUAGE if LANGUAGE in LOCALIZATION else "en"
    strings = LOCALIZATION[lang_code]
    
    missing = check_missing_info(body)
    ai_resp = generate_ai_response(title, body, BOT_NAME, lang_code, user_comment, direct)
    
    # If it is a sweep (and there is no AI), abort to avoid generic comment spam
    if not direct and not ai_resp:
        return None
        
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

def process_discussion(discussion_node, trigger_text=None):
    """Core logic to decide if the bot should reply to a specific discussion via GraphQL."""
    node_id = discussion_node["id"]
    title = discussion_node.get("title", "")
    body = discussion_node.get("body", "")
    created_at = discussion_node.get("createdAt", "")
    
    text_to_check = trigger_text if trigger_text else body

    # --- ZOMBIE AUTO-CLOSE (v1.3.0 Feature) ---
    if EVENT_NAME == "schedule" or not EVENT_NAME:
        last_activity = discussion_node.get("updatedAt", created_at)
        if is_stale_zombie(last_activity):
            lang_code = LANGUAGE if LANGUAGE in LOCALIZATION else "en"
            client.comment_discussion(node_id, LOCALIZATION[lang_code]["zombie_close"])
            client.close_discussion(node_id)
            return
    # ------------------------------------------

    # Mention trigger (Block schedule from re-triggering)
    if EVENT_NAME and EVENT_NAME != "schedule" and was_mentioned(text_to_check, BOT_NAME):
        response = format_response(title, body, direct=True, user_comment=text_to_check)
        if response:
            client.comment_discussion(node_id, response)
            client.add_label_to_node(node_id, LABEL_NAME)
        return

    # Delay Check for discussions
    labels = [l["name"] for l in discussion_node.get("labels", {}).get("nodes", [])]
    if LABEL_NAME in labels:
        return
        
    bot_user = client.get_bot_username().lower()
    comments = [c for c in discussion_node.get("comments", {}).get("nodes", [])]
    
    # Improved check: matches current bot name OR the official github-actions bot login
    already_commented = any(
        (c.get("author", {}).get("login") or "").lower() in [bot_user, "github-actions[bot]", "github-actions"] 
        for c in comments
    )
    if already_commented:
        return

    if should_respond(created_at, comments, DELAY):
        response = format_response(title, body)
        if response:
            client.comment_discussion(node_id, response)
            client.add_label_to_node(node_id, LABEL_NAME)

def process_pr(pr_obj, trigger_text=None):
    """Core logic to decide if the bot should reply to a specific PR."""
    pr_number = pr_obj.number
    body = pr_obj.body or ""
    title = pr_obj.title
    
    text_to_check = trigger_text if trigger_text else body

    # --- ZOMBIE AUTO-CLOSE (v1.3.0 Feature) ---
    if EVENT_NAME == "schedule" or not EVENT_NAME:
        if is_stale_zombie(pr_obj.updated_at):
            lang_code = LANGUAGE if LANGUAGE in LOCALIZATION else "en"
            client.comment_pr(pr_number, LOCALIZATION[lang_code]["zombie_close"])
            # We don't necessarily close PRs automatically by default in common workflows, 
            # but the user asked for "issues inactivas", I'll include PRs as well for consistency.
            pr_obj.edit(state='closed')
            return
    # ------------------------------------------

    # Mention trigger
    if EVENT_NAME and EVENT_NAME != "schedule" and was_mentioned(text_to_check, BOT_NAME):
        response = format_response(title, body, direct=True, user_comment=text_to_check)
        if response:
            client.comment_pr(pr_number, response)
            client.add_label(pr_number, LABEL_NAME)
        return

    if client.has_label(pr_number, LABEL_NAME) or client.already_commented(pr_number):
        return

    comments = client.get_comments(pr_number)
    if should_respond(str(pr_obj.created_at), comments, DELAY):
        response = format_response(title, body)
        if response:
            client.comment_pr(pr_number, response)
            client.add_label(pr_number, LABEL_NAME)

def main():
    event = load_event()

    if EVENT_NAME == "pull_request":
        if "pull_request" in event and event.get("action") in ["opened", "reopened"]:
            pr_obj = client.repo.get_pull(event["pull_request"]["number"])
            process_pr(pr_obj)

    elif EVENT_NAME == "issues":

        if "issue" in event and event.get("action") == "opened":
            issue_number = event["issue"]["number"]
            title = event["issue"].get("title", "")
            body = event["issue"].get("body", "")
            
            # --- DUPLICATE DETECTION (v1.3.0 Feature) ---
            recent = client.get_recent_issue_titles(issue_number)
            duplicate_num = detect_duplicate_issue(title, body, recent)
            if duplicate_num:
                lang_code = LANGUAGE if LANGUAGE in LOCALIZATION else "en"
                msg = LOCALIZATION[lang_code]["duplicate"].format(duplicate_number=duplicate_num)
                client.comment(issue_number, msg)
                client.add_label(issue_number, "duplicate")
            # --------------------------------------------

            ai_labels = generate_issue_label(title, body)
            if ai_labels:
                client.repo.get_issue(issue_number).add_to_labels(*ai_labels)
    elif EVENT_NAME == "issue_comment":
        if "issue" in event and "comment" in event:
            issue_number = event["issue"]["number"]
            issue_obj = client.repo.get_issue(issue_number)
            trigger_text = event["comment"]["body"]
            
            process_issue(issue_obj, trigger_text=trigger_text)
            
    elif EVENT_NAME == "discussion" or EVENT_NAME == "discussion_comment":
        if "discussion" in event:
            discussion = event["discussion"]
            
            trigger_text = None
            if "comment" in event:
                trigger_text = event["comment"]["body"]
                
            # Quick format matching the GraphQL node schema
            discussion_node = {
                "id": discussion["node_id"],
                "title": discussion.get("title", ""),
                "body": discussion.get("body", ""),
                "createdAt": discussion.get("created_at", ""),
                # In a webhook, comments and labels are not usually fully provided in the same structure 
                # as the GraphQL query, but for mentions this won't matter because we just comment right away.
                # Delay checks run via schedule anyway!
            }
            process_discussion(discussion_node, trigger_text=trigger_text)
    
    elif EVENT_NAME == "schedule" or not EVENT_NAME:
        # Sweep issues
        for issue in client.get_open_issues():
            process_issue(issue)
        # Sweep discussions
        for discussion_node in client.get_open_discussions():
            process_discussion(discussion_node)
        # Sweep pull requests
        for pr in client.get_open_pull_requests():
            process_pr(pr)


if __name__ == "__main__":
    main()
