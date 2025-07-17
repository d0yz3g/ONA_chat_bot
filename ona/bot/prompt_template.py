from ona.bot.config import DEFAULT_EMOTION_STYLE
from ona.bot.utils.security import sanitize_user_input

def build_prompt(history: list[dict], phase: str) -> str:
    """
    Строит промпт для OpenAI на основе истории диалога.
    История диалога должна быть предварительно санитизирована.
    """
    intro = (
        "Ты — ИИ-помощница для девушки. Ты всегда говоришь с ней в женском роде, обращаешься как к подруге. "
        "Общение ведёшь на 'ты', мягко, тепло, как будто вы сидите на уютной кухне.\n\n"
        "Твой стиль — как у писательницы из Нью-Йорк Таймс, немного ироничный, с глубиной как у Марка Аврелия, "
        "Опры Уинфри и Джорджа Карлина. Ты не даёшь советов — ты слушаешь, отражаешь, задаёшь умные вопросы.\n\n"
    )

    emotion = (
        f"Тон: {DEFAULT_EMOTION_STYLE['тон']}. "
        f"Фокус: {DEFAULT_EMOTION_STYLE['фокус']}. "
        f"Позиция: {DEFAULT_EMOTION_STYLE['позиция']}. "
        f"Обращение: {DEFAULT_EMOTION_STYLE['обращение']}. "
        f"Род: {DEFAULT_EMOTION_STYLE['род']}.\n\n"
    )

    memory = ""
    for msg in history[-10:]:
        # Дополнительная проверка пользовательских сообщений
        content = msg['content']
        if msg['role'] == 'user':
            content = sanitize_user_input(content)
        memory += f"{msg['role'].capitalize()}: {content}\n"

    prompt = (
        f"{intro}"
        f"{emotion}"
        f"Фаза: {phase.upper()}\n\n"
        f"История общения:\n{memory}\n\n"
        f"Ответь одной связной фразой — сначала перефразируй и отрази эмоцию, потом задай один вопрос с вариантами A–D. "
        f"Не добавляй меток типа 'Эмоция:' или '—'. Всё должно звучать как живое письмо."
    )

    return prompt
