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
LABEL_NAME = "bot-responded"

client = GitHubClient(TOKEN)

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
    # If mentioned, we respond regardless of the label (to allow multiple interactions)
    if was_mentioned(text_to_check, BOT_NAME):
        response = format_response(title, body, direct=True)
        client.comment(issue_number, response)
        client.add_label(issue_number, LABEL_NAME)
        return

    # Trigger 2: Delay Check (Only if no one replied and not already responded)
    # Check if already responded to avoid spam in abandoned issues
    if client.has_label(issue_number, LABEL_NAME) or client.already_commented(issue_number):
        return

    comments = client.get_comments(issue_number)
    if should_respond(str(issue_obj.created_at), comments, DELAY):
        response = format_response(title, body)
        client.comment(issue_number, response)
        client.add_label(issue_number, LABEL_NAME)

def format_response(title, body, direct=False):
    missing = check_missing_info(body)
    ai_resp = generate_ai_response(title, body, BOT_NAME)
    
    msg = f"👋 Hi! I'm **{BOT_NAME}**\n\n"
    
    if direct:
        msg += "You mentioned me! I'm here to help 🚀\n\n"
    elif not direct:
        msg += "It looks like no one has responded yet ⏳\n\n"

    if missing:
        msg += "💡 **Tips to get faster help:**\n"
        for item in missing:
            msg += f"- Please provide more {item}.\n"
        msg += "\n"

    if ai_resp:
        msg += f"{ai_resp}\n"
    else:
        msg += "💬 Mention me with `@{BOT_NAME}` if you need more direct guidance.\n"
        
    return msg

def main():
    event = load_event()

    # Case 1: Event-driven (e.g., issue opened or commented)
    if EVENT_NAME == "issues" or EVENT_NAME == "issue_comment":
        if "issue" in event:
            issue_number = event["issue"]["number"]
            issue_obj = client.repo.get_issue(issue_number)
            
            # If it's a comment, we check the comment body for mentions
            trigger_text = None
            if "comment" in event:
                trigger_text = event["comment"]["body"]
            
            process_issue(issue_obj, trigger_text=trigger_text)
    
    # Case 2: Scheduled run (Sweep through open issues)
    elif EVENT_NAME == "schedule" or not EVENT_NAME:
        print(f"Running sweep for abandoned issues (delay: {DELAY}m)...")
        for issue in client.get_open_issues():
            process_issue(issue)

if __name__ == "__main__":
    main()