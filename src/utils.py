from datetime import datetime, timezone

def should_respond(created_at_str, comments, delay_minutes):
    created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)

    diff = (now - created_at).total_seconds() / 60

    if diff < delay_minutes:
        return False

    return len(comments) == 0


def was_mentioned(text, bot_name):
    if not text:
        return False

    return f"@{bot_name}".lower() in text.lower()


def check_missing_info(issue_body):
    """Checks if the issue body is missing common debug info."""
    if not issue_body:
        return ["description"]
    
    missing = []
    
    # Check for code blocks or logs
    if "```" not in issue_body:
        missing.append("code blocks or logs")
    
    # Check for minimal length
    if len(issue_body) < 50:
        missing.append("detailed explanation")
        
    return missing