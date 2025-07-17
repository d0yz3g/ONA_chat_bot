from ona.bot.supabase_service import get_user_data, save_user_data
from openai import OpenAI
from ona.bot.config import OPENAI_API_KEY
from ona.bot.utils.security import sanitize_user_input

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_user_summary(user_id: int) -> str:
    user_data = get_user_data(user_id)
    # Имя уже должно быть санитизировано при сохранении
    name = user_data.get("name", "ты")
    history = user_data.get("history", [])

    # Формируем историю для анализа
    # История уже должна быть санитизирована при сохранении
    dialog = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in history])

    # Промпт для глубокого анализа
    prompt = (
        "Ты — опытный психолог, коуч и писательница. На основе следующего диалога "
        "сделай краткий, но глубокий анализ состояния, тем, эмоций и целей человека. "
        "Определи, с чем он пришёл, что его беспокоило, какие выводы сделал и какие ресурсы у него есть. "
        "Говори в тоне поддержки, уверенности и уважения. Не пересказывай диалог буквально, а сделай суть.\n\n"
        f"Имя пользователя: {name}\n\n"
        f"Диалог:\n{dialog}\n\n"
        f"Выведи итог одним блоком текста."
    )

    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.7,
        max_tokens=500,
    )

    summary = completion.choices[0].message.content.strip()
    # Ответ от GPT не нужно санитизировать
    save_user_data(user_id, "summary", summary)
    return summary
