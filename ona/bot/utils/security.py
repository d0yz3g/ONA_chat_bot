import re
import html

def sanitize_user_input(text: str) -> str:
    """
    Надёжно очищает пользовательский ввод от XSS, prompt injection и других вредоносных конструкций.

    Args:
        text (str): Ввод пользователя

    Returns:
        str: Очищенный и безопасный текст
    """
    # 1. Декодируем HTML-сущности (например, &lt; -> <)
    text = html.unescape(text)

    # 2. Удаляем HTML-теги (XSS)
    text = re.sub(r"<[^>]+>", "", text)

    # 3. Удаляем шаблоны вроде {{...}} (prompt injection)
    text = re.sub(r"\{\{.*?\}\}", "", text)

    # 4. Удаляем чувствительные паттерны (можно дополнять)
    danger_patterns = [
        r"(?i)alert\s*\(",
        r"(?i)system\s*\(",
        r"(?i)exec\s*\(",
        r"(?i)rm\s+-rf",
        r"(?i)curl\s+",
        r"(?i)wget\s+",
        r"--",
        r"\bselect\b",
        r"\bdrop\b",
        r"\binsert\b",
        r"\n\nAssistant:",
        r"\n\nUser:"
    ]
    for pattern in danger_patterns:
        text = re.sub(pattern, "[filtered]", text)

    # 5. Финальное экранирование (если надо сохранить < > как текст)
    text = html.escape(text)

    return text.strip()
