from openai import OpenAI
from ona.bot.config import OPENAI_API_KEY
from typing import List, Tuple

client = OpenAI(api_key=OPENAI_API_KEY)

def _generate_questions(prompt: str, max_questions: int = 2) -> List[Tuple[str, List[str]]]:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.75,
        max_tokens=600,
    ).choices[0].message.content.strip()

    blocks = response.split("\n\n")
    results = []

    for block in blocks[:max_questions]:
        lines = block.strip().splitlines()
        if len(lines) >= 6:
            question = lines[0].strip()
            options = [line.strip() for line in lines[1:6]]
            results.append((question, options))

    return results


def explore_resources(topic: str, user_history: List[str]) -> List[Tuple[str, List[str]]]:
    joined_history = "\n".join(f"- {msg}" for msg in user_history[-6:])

    prompt = f"""
Ты — ИИ-помощница. Сейчас ФАЗА 4.1: Поиск ресурсов.

Ты помогаешь человеку:
- вспомнить моменты, когда он уже справлялся с похожим
- осознать, кто может быть источником поддержки
- почувствовать свои сильные стороны и то, что даёт энергию

Контекст — это тема, над которой работает человек: "{topic}"

Вот последние сообщения пользователя:
{joined_history}

Сформулируй 2 или 3 коротких вопроса (не больше), каждый с 5 вариантами ответов A–E.

⚠️ Вопросы должны быть логическим продолжением того, что человек уже написал.
⚠️ Не используй шаблоны. Не пиши "Вопрос:", "[вопрос 1]" и т.п.
⚠️ Варианты должны звучать естественно и быть уместными.
⚠️ Не дублируй и не повторяй формулировки.

Формат:
[вопрос 1]
A) ...
B) ...
C) ...
D) ...
E) ...

[вопрос 2]
A) ...
...
"""
    results = _generate_questions(prompt, max_questions=3)

    if not results:
        fallback_question = "Когда ты уже справлялась с похожей ситуацией раньше?"
        fallback_options = [
            "A) В детстве",
            "B) Недавно",
            "C) Давно",
            "D) Не уверена",
            "E) Могу рассказать"
        ]
        results.append((fallback_question, fallback_options))

    return results


def collaborative_planning(topic: str, user_history: List[str]) -> List[Tuple[str, List[str]]]:
    joined_history = "\n".join(f"- {msg}" for msg in user_history[-6:])

    prompt = f"""
Ты — ИИ-помощница. Сейчас ФАЗА 4.2: Совместное планирование.

Контекст: тема разговора — "{topic}"

Вот выдержка из последних сообщений:
{joined_history}

Сформулируй 2 коротких вопроса, чтобы помочь человеку перейти к действию.
⚠️ Не используй шаблонные фразы. Построй вопросы как естественное продолжение диалога.
⚠️ Не пиши заголовки или префиксы ("Вопрос:" и т.п.)
⚠️ Каждый вопрос должен сопровождаться 5 вариантами ответа (A–E)
⚠️ Говори на "ты", дружелюбно и без давления

Формат:
[вопрос 1]
A) ...
B) ...
C) ...
D) ...
E) ...

[вопрос 2]
A) ...
...
"""
    return _generate_questions(prompt, max_questions=2)


# 👇 ДОБАВЬ ВОТ ТАК — через 1 пустую строку после предыдущей функции
def get_all_phase_4_questions(topic: str, user_history: List[str]) -> dict:
    return {
        "resources": explore_resources(topic, user_history),
        "planning": collaborative_planning(topic, user_history)
    }
