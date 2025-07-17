from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def get_context_options() -> tuple[str, list[str]]:
    prompt = '''
Ты — ИИ-помощница, ведущая первый диалог с новым человеком.

Сгенерируй вступительный вопрос в стиле:
- "Что тебе сейчас важно обсудить?"
- дружелюбный, доверительный, без экспертности
- добавь 4 варианта ответов в формате A) ... D)

Пример:
Что тебе сейчас важно обсудить?
A) Хочешь поговорить о том, что тебя беспокоит?
B) Может, есть какая-то ситуация, которую хочешь разобрать?
C) Или просто нужна поддержка прямо сейчас?
D) А может, твой вариант?

Ответ верни строго в таком же формате — строка вопроса, потом 4 строки A)–D)
'''
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

def initial_greeting(name: str) -> str:
    return (
        f"{name}... Как будто имя уже само по себе из романа.\n"
        f"Очень приятно, что ты здесь. Я рядом — без осуждения, без советов «сверху». "
        f"Только ты, я, и пространство, где можно выдохнуть."
    )
