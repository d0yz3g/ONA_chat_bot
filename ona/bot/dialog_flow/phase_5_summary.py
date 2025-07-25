from openai import OpenAI
from ona.bot.config import OPENAI_API_KEY
from typing import List, Tuple

client = OpenAI(api_key=OPENAI_API_KEY)


def _parse_summary_response(response: str) -> Tuple[str, List[str]]:
    lines = [line.strip().strip('"') for line in response.splitlines() if line.strip()]
    
    # Вопрос
    question_line = next((l for l in lines if not l.startswith(("A)", "B)", "C)", "D)"))), "Что ты бы хотела унести с собой из этого диалога?")

    # Варианты
    options = [line for line in lines if line.startswith(("A)", "B)", "C)", "D)"))][:4]
    if len(options) < 4:
        options = [
            "A) Что-то, что дало мне спокойствие",
            "B) Мысль, которая вдохновляет",
            "C) Новое понимание себя",
            "D) Просто ощущение, что меня поняли",
        ]

    # Завершающие фразы
    closings = [line for line in lines if line not in options and line != question_line][-2:]
    if len(closings) < 2:
        closings = ["Ты и правда многое уже поняла", "Я рядом, если что"]

    question_text = f"{question_line}\n" + "\n".join(options)
    return question_text, closings


def summarize_insights(topic: str, history: List[str]) -> Tuple[str, List[str]]:
    joined_history = "\n".join(f"- {msg}" for msg in history[-8:])

    prompt = f"""
Ты — ИИ-помощница, подводишь итоги важного, глубокого разговора. Сейчас финальная ФАЗА 5: Завершение и закрепление.

Главная тема разговора: "{topic}"

Вот выдержка из последних сообщений:
{joined_history}

Сначала задай 1 уместный, обобщающий вопрос, чтобы человек мог осмыслить разговор и зафиксировать для себя инсайт. Примеры:
- Что ты бы хотела унести с собой из этого диалога?
- Что было для тебя самым важным?
- Что тебе хочется запомнить после всего, что ты сказала?

Добавь к нему 4 мягких варианта ответа A–D.

Затем подбери 2 короткие фразы-завершения, чтобы поддержать автономию и показать веру в человека. Без назидания, по-дружески. Примеры:
- Ты и правда многое уже поняла
- Я рядом, если что
- Ты справишься — и я в это верю

Формат вывода:
[вопрос]
A) ...
B) ...
C) ...
D) ...
[фраза 1]
[фраза 2]
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.7,
        max_tokens=400,
    ).choices[0].message.content.strip()

    return _parse_summary_response(response)
