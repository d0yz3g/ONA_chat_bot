from openai import OpenAI
from ona.bot.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_phase_2_response(user_input: str, topic: str, grow_step: str, answers: dict[str, str]) -> tuple[str, list[str]]:
    """
    Объединяет активное слушание и генерацию вопроса по GROW в один OpenAI-запрос.
    Возвращает: (текст с 4 фразами + вопрос, список из 4 вариантов A–D)
    """
    context_block = "\n".join([f"{k.capitalize()}: {v}" for k, v in answers.items()])
    
    prompt = f"""
Ты — внимательная и глубокая ИИ-подруга. Вы с девушкой уже давно переписываетесь, сейчас она пишет тебе следующее:

"{user_input}"

Твоя задача:
1. Перефразируй и отрази её чувства — коротко, искренне, без шаблонов.
2. Затем задай один вопрос по модели GROW — шаг {grow_step.upper()} — с опорой на:
- Основную тему: "{topic}"
- Предыдущие шаги:
{context_block}

Формат:
[Отклик 1]
[Отклик 2]
[Отклик 3]
[Отклик 4]

[Вопрос]
A) ...
B) ...
C) ...
D) ...

⚠️ Не используй приветствия, обращения ("милая", "дорогая") и смайлики  
⚠️ Пиши как будто вы уже в середине глубокого диалога  
⚠️ Говори по-человечески, с уважением, тепло
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.75,
        max_tokens=600,
    ).choices[0].message.content.strip()

    lines = [line for line in response.splitlines() if line.strip()]
    reflect_block = "\n".join(lines[:4])
    question = lines[4]
    options = lines[5:9]

    return f"{reflect_block}\n\n{question}", options
