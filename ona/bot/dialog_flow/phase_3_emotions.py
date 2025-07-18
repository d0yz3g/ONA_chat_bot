from openai import OpenAI
from ona.bot.config import OPENAI_API_KEY
from ona.bot.supabase_service import get_user_data
from ona.bot.safety import detect_crisis
from ona.bot.utils.security import sanitize_user_input

client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_emotion_and_thinking(user_id: int, user_text: str) -> str:
    """
    Анализирует сообщение на наличие сильных эмоций или когнитивных искажений.
    Возвращает: "emotion", "distortion" или "none"
    """
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
    return response.choices[0].message.content.strip().lower()


def generate_phase_3_response(step: str, user_input: str | None = None) -> tuple[str, list[str]]:
    """
    Генерация вопроса и вариантов на основе текущего шага:
    - step = "emotion", "meaning", "cognitive_1", "cognitive_2"
    """
    instruction_map = {
        "emotion": "Спроси мягко: Что стоит за этим чувством?",
        "meaning": "Спроси: О чём может говорить это чувство?",
        "cognitive_1": "Спроси: Что бы ты сказала подруге в такой ситуации?",
        "cognitive_2": "Спроси: Какие у тебя есть доказательства за и против?",
    }

    instruction = instruction_map.get(step)
    if not instruction:
        raise ValueError(f"Unknown step: {step}")

    prompt = f"""
Ты — ИИ-помощница. Пользователь проходит эмоциональный анализ (фаза 3).

{instruction}
Добавь 4 варианта ответа (A–D), без пояснений, на ты.

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
