from supabase import create_client, Client
from ona.bot.config import SUPABASE_URL, SUPABASE_KEY
from ona.bot.utils.security import sanitize_user_input

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_user_data(user_id: int, key: str, value: str):
    """
    Сохраняет данные пользователя в Supabase.
    Все пользовательские данные должны быть предварительно санитизированы.
    """
    # Дополнительная проверка для пользовательских данных
    if key in ["name", "topic", "summary", "emotion", "readiness", "request_type"]:
        value = sanitize_user_input(value)
        
    data = {"user_id": user_id, key: value}
    existing = (
        supabase.table("users")
        .select("id")
        .eq("user_id", user_id)
        .execute()
    )
    if existing.data:
        supabase.table("users").update({key: value}).eq("user_id", user_id).execute()
    else:
        if key != "summary":
            data["summary"] = ""
        supabase.table("users").insert(data).execute()

def get_user_data(user_id: int) -> dict:
    """
    Получает данные пользователя из Supabase.
    """
    res = (
        supabase.table("users")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )
    if res.data:
        return res.data[0]
    return {}

def append_dialog_history(user_id: int, message: str, role: str):
    """
    Добавляет сообщение в историю диалога.
    Пользовательские сообщения (role == 'user') должны быть предварительно санитизированы.
    """
    history = get_user_data(user_id).get("history", [])
    if not isinstance(history, list):
        history = []
        
    # Дополнительная проверка для пользовательских сообщений
    if role == "user":
        message = sanitize_user_input(message)
        
    history.append({"role": role, "content": message})
    supabase.table("users").update({"history": history}).eq("user_id", user_id).execute()

def save_user_traits(user_id: int, emotion: str, readiness: str, request_type: str):
    """
    Сохраняет характеристики пользователя.
    Все входные данные должны быть предварительно санитизированы.
    """
    # Дополнительная проверка всех пользовательских данных
    emotion = sanitize_user_input(emotion)
    readiness = sanitize_user_input(readiness)
    request_type = sanitize_user_input(request_type)
    
    supabase.table("users").update({
        "emotion": emotion,
        "readiness": readiness,
        "request_type": request_type
    }).eq("user_id", user_id).execute()

def bulk_save_user_data(user_id: int, updates: dict):
    """
    Обновляет несколько полей пользователя одним PATCH-запросом.
    """
    sanitized = {
        key: sanitize_user_input(value) if isinstance(value, str) else value
        for key, value in updates.items()
    }
    supabase.table("users").update(sanitized).eq("user_id", user_id).execute()

