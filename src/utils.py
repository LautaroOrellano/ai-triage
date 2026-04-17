from datetime import datetime, timezone

def should_respond(created_at_str, comments, delay_minutes):
    now = datetime.now(timezone.utc)
    
    # REGLA 2: "solo por un comentario nuevo, no por el issue principal"
    # Si no hay comentarios, ignorar el issue por completo.
    if len(comments) == 0:
        return False
        
    # Obtener el último comentario creado
    # PyGithub comments ya vienen ordenados cronológicamente, pero aseguramos
    last_comment = comments[-1]
    
    # Extraer la fecha del comentario, que para REST/GraphQL puede venir como string o como objeto datetime 
    # (PyGithub usa objetos datetime, GraphQL usamos strings)
    try:
        if isinstance(last_comment, dict):
            last_created = last_comment.get("createdAt")
            if not last_created: return False
            last_time = datetime.fromisoformat(last_created.replace("Z", "+00:00"))
        else:
            last_time = last_comment.created_at
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=timezone.utc)
    except:
        return False

    diff = (now - last_time).total_seconds() / 60

    # Retraso (ej: 60 minutos)
    if diff < delay_minutes:
        return False
        
    # REGLA FANTASMA: Ignorar el comentario si tiene más de 7 días (para no reanimar zombies)
    if diff > 10080:
        return False

    return True


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
        missing.append("logs")
    
    # Check for minimal length
    if len(issue_body) < 50:
        missing.append("details")
        
    return missing

def is_stale_zombie(last_updated_at, years=2):
    """Checks if an issue has been inactive for more than X years."""
    now = datetime.now(timezone.utc)
    
    # Handle both datetime objects and ISO strings
    if isinstance(last_updated_at, str):
        last_time = datetime.fromisoformat(last_updated_at.replace("Z", "+00:00"))
    else:
        last_time = last_updated_at
        if last_time.tzinfo is None:
            last_time = last_time.replace(tzinfo=timezone.utc)
            
    diff_days = (now - last_time).days
    return diff_days > (years * 365)