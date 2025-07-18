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
Ты — внимательная и заботливая ИИ-подруга. Твоя задача:

1. Отреагировать на сообщение подруги с активным слушанием — 4 короткие фразы, как будто ты пишешь четырём близким подругам в разных стилях.

2. Затем — задать один вопрос по модели GROW, соответствующий шагу {grow_step.upper()}, опираясь на:
- Основную тему: "{topic}"
- Предыдущие шаги:
{context_block}

Добавь к вопросу 4 варианта A–D.

Формат:
[Фраза 1]
[Фраза 2]
[Фраза 3]
[Фраза 4]

[Вопрос]
A) ...
B) ...
C) ...
D) ...
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
