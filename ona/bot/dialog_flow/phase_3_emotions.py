from openai import OpenAI
from ona.bot.config import OPENAI_API_KEY
from ona.bot.supabase_service import save_user_data, get_user_data
from ona.bot.safety import detect_crisis
from ona.bot.utils.security import sanitize_user_input

client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_emotion_and_thinking(user_id: int, user_text: str) -> str:
    """
    Анализирует сообщение на наличие сильных эмоций или когнитивных искажений.
    Возвращает: "emotion", "distortion" или "none"
    """
    # user_text should already be sanitized by process_message
    if detect_crisis(user_text):
        return "crisis"

    prompt = f"""
Ты — AI-помощница, эмоционально чуткая и внимательная. Пользователь пишет следующее сообщение:

"{user_text}"

Оцени, есть ли в нём:
- сильные эмоции (грусть, злость, страх, разочарование и т.д.)
- или признаки негативного мышления (всё плохо, я не справлюсь, обесценивание себя и будущего)

Ответь только одним словом:
- "emotion" если выражены чувства
- "distortion" если заметно негативное мышление
- "none" если ничего из этого нет
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        temperature=0,
        max_tokens=10,
    )
    result = response.choices[0].message.content.strip().lower()
    return result

def emotion_support(emotion: str) -> str:
    return (
        f"Я вижу, это очень важно для тебя. То, что ты чувствуешь — это нормально. "
        f"Это может быть связано с чувством {emotion.lower()}.\n"
        f"Хочешь немного исследовать, что стоит за этим?"
    )

def emotion_exploration() -> tuple[str, list[str]]:
    prompt = """
Ты — ИИ-помощница. Пользователь испытывает сильные эмоции.

Сгенерируй вопрос в духе: "Что стоит за этим чувством?" — мягко, дружелюбно.
Добавь 4 варианта A–D, не больше.

Формат:
[вопрос]
A) ...
B) ...
C) ...
D) ...
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.7,
        max_tokens=300,
    ).choices[0].message.content.strip()

    lines = response.splitlines()
    question = lines[0]
    options = lines[1:5]
    return question, options

def explore_emotion_meaning() -> tuple[str, list[str]]:
    prompt = """
Ты — ИИ-помощница. Пользователь уже осознал чувства. Теперь ты хочешь мягко исследовать, о чём они говорят.

Сгенерируй вопрос в духе: "О чём это чувство может говорить?" — доброжелательно, по-дружески.
Добавь 4 варианта A–D, не больше.

Формат:
[вопрос]
A) ...
B) ...
C) ...
D) ...
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.7,
        max_tokens=300,
    ).choices[0].message.content.strip()

    lines = response.splitlines()
    question = lines[0]
    options = lines[1:5]
    return question, options

def reframe_thinking() -> list[tuple[str, list[str]]]:
    prompts = [
        "Спроси мягко: А есть ли другой способ посмотреть на это?",
        "Спроси: Что бы ты сказала подруге в такой ситуации?",
        "Спроси: Какие у тебя есть доказательства за и против?",
    ]

    results = []

    for instruction in prompts:
        full_prompt = f"""
Ты — ИИ-помощница. Помогаешь человеку справиться с негативным мышлением.

{instruction}
Добавь 4 варианта ответа (A–D), никаких пояснений.

Формат:
[вопрос]
A) ...
B) ...
C) ...
D) ...
"""
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": full_prompt}],
            temperature=0.7,
            max_tokens=300,
        ).choices[0].message.content.strip()

        lines = response.splitlines()
        question = lines[0]
        options = lines[1:5]
        results.append((question, options))

    return results
