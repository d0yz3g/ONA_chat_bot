import asyncio
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.methods import SendChatAction
from ona.bot.state import DialogState
from ona.bot.prompt_template import build_prompt
from ona.bot.safety import detect_crisis, generate_crisis_response
from ona.bot.supabase_service import (
    save_user_data,
    append_dialog_history,
    get_user_data,
    bulk_save_user_data,  # ← добавлено для объединённого PATCH
)
from ona.bot.core.openai_client import client
from ona.bot.analysis import generate_user_summary
from ona.bot.dialog_flow.phase_2_listen import grow_questions, reflective_listening
from ona.bot.dialog_flow.phase_3_emotions import (
    emotion_exploration,
    explore_emotion_meaning,
    reframe_thinking,
    analyze_emotion_and_thinking,
)
from ona.bot.dialog_flow.phase_4_solutions import explore_resources, collaborative_planning
from ona.bot.dialog_flow.phase_5_summary import summarize_insights
from ona.bot.utils.security import sanitize_user_input
from ona.bot.dialog_flow.phase_2_response import generate_phase_2_response  # вверху файла

PHASE_ORDER = [
    DialogState.phase_1_init,
    DialogState.phase_2_listen,
    DialogState.phase_3_emotions,
    DialogState.phase_4_solutions,
    DialogState.phase_5_summary,
]

GROW_SEQUENCE = ["goal", "reality", "options", "will"]


async def process_message(message: Message, state: FSMContext, user_input: str | None = None):
    user_id = message.from_user.id
    user_input = sanitize_user_input((user_input or message.text).strip())
    current_state = await state.get_state()
    user_data = get_user_data(user_id)

    if current_state is None:
        await state.set_state(DialogState.ask_name)
        await message.answer(
            "Привет, дорогая 🌿\n"
            "Давай сделаем тебе уютное место здесь — будто мы сидим на кухне, а из чайника идёт пар. "
            "Я рядом, чтобы выслушать, понять и быть с тобой на одной волне.\n"
            "Как тебя зовут, чтобы я могла обращаться по имени?"
        )
        return

    if current_state == DialogState.ask_name.state:
        name = user_input  # Already sanitized
        save_user_data(user_id, "name", name)
        append_dialog_history(user_id, name, "user")
        greeting = generate_unique_greeting(name)
        context_question, options = generate_context_question()
        full_text = f"{greeting}\n\n{context_question}\n" + "\n".join(options)
        await state.update_data(last_options=[opt[3:].strip() for opt in options])
        append_dialog_history(user_id, full_text, "assistant")
        await message.bot(SendChatAction(chat_id=message.chat.id, action="typing"))
        await message.answer(full_text)
        await state.set_state(DialogState.phase_2_listen)
        save_user_data(user_id, "grow_step", "goal")
        save_user_data(user_id, "topic", "")
        return

    if detect_crisis(user_input):
        await state.set_state(DialogState.crisis)
        await message.answer(generate_crisis_response())
        return

    if current_state == DialogState.crisis.state:
        append_dialog_history(user_id, user_input, "user")
        history = get_dialog_history(user_id)
        prompt = (
            "Ты — ИИ-помощница. Пользователь в кризисе. "
            "Говори мягко и с заботой. Без советов. Без шаблонов. Без вопросов с вариантами.\n\n"
            "История последних сообщений:\n" +
            "\n".join([f"{m['role']}: {m['content']}" for m in history[-5:]])
        )
        response = generate_ai_response(prompt)
        append_dialog_history(user_id, response, "assistant")
        await message.answer(response)
        return

    if current_state == DialogState.completed.state:
        append_dialog_history(user_id, user_input, "user")

        summary = user_data.get("summary", "").strip()
        history = user_data.get("history", [])

        prompt = (
            "Ты — заботливая AI-подруга, с которой можно поговорить о чём угодно. "
            "Ты не эксперт и не даёшь советов — ты слушаешь, поддерживаешь и говоришь по-человечески. "
            "Вот краткий анализ того, что уже обсуждалось:\n"
            f"{summary}\n\n"
            "Вот выдержка из последних сообщений между вами:\n" +
            "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in history[-20:]]) +
            "\n\nОтветь искренне, тёпло и естественно — без шаблонов и без вариантов ответа. Просто продолжи разговор."
        )

        response = generate_ai_response(prompt)
        append_dialog_history(user_id, response, "assistant")
        await message.answer(response)
        return

    append_dialog_history(user_id, user_input, "user")
    phase = next((s for s in PHASE_ORDER if s.state == current_state), DialogState.phase_1_init)
    await message.bot(SendChatAction(chat_id=message.chat.id, action="typing"))

    if phase == DialogState.phase_2_listen:
        current_grow = user_data.get("grow_step", "goal")
        topic = user_data.get("topic", "")

        # Сохраняем текущий ответ
        save_user_data(user_id, f"grow_{current_grow}", user_input)

        # Если это первая фраза → запоминаем как тему
        if current_grow == "goal" and not topic:
            save_user_data(user_id, "topic", user_input)
            topic = user_input

        # Собираем все предыдущие grow-ответы
        answers = {}
        for step in GROW_SEQUENCE:
            val = user_data.get(f"grow_{step}")
            if val:
                answers[step] = val

        question_block, options = generate_phase_2_response(user_input, topic, current_grow, answers)
        text = f"{question_block}\n" + "\n".join(options)
        await state.update_data(last_options=[opt[3:].strip() for opt in options])
        append_dialog_history(user_id, text, "assistant")
        await message.answer(text)

        # Переход к следующей стадии GROW или к фазе 3
        idx = GROW_SEQUENCE.index(current_grow)
        if idx + 1 < len(GROW_SEQUENCE):
            save_user_data(user_id, "grow_step", GROW_SEQUENCE[idx + 1])
            await state.set_state(DialogState.phase_2_listen)
        else:
            save_user_data(user_id, "grow_step", None)
            save_user_data(user_id, "emotion_step", "start")
            await state.set_state(DialogState.phase_3_emotions)
        return

    if phase == DialogState.phase_3_emotions:
        emotion_step = user_data.get("emotion_step", "start")

        if emotion_step == "start":
            result = analyze_emotion_and_thinking(user_id, user_input)
            if result == "emotion":
                save_user_data(user_id, "emotion_step", "meaning")
                question, options = emotion_exploration()
                text = f"Я вижу, это очень важно для тебя. Это естественная реакция на такую ситуацию.\n\n{question}\n" + "\n".join(options)
                await state.update_data(last_options=[opt[3:].strip() for opt in options])
                append_dialog_history(user_id, text, "assistant")
                await message.answer(text)
                return
            elif result == "distortion":
                save_user_data(user_id, "emotion_step", "cognitive_1")
                blocks = reframe_thinking()
                question, options = blocks[0]
                text = f"{question}\n" + "\n".join(options)
                append_dialog_history(user_id, text, "assistant")
                await message.answer(text)
                return
            else:
                await state.set_state(DialogState.phase_4_solutions)
                save_user_data(user_id, "resource_step", "resources")
                topic = user_data.get("topic", "")
                history = [m["content"] for m in get_dialog_history(user_id) if m["role"] == "user"]
                questions = explore_resources(topic, history)
                question, options = questions[0]
                text = f"{question}\n" + "\n".join(options)
                append_dialog_history(user_id, text, "assistant")
                await message.answer(text)
                return

        elif emotion_step == "meaning":
            save_user_data(user_id, "emotion_step", "done")
            question, options = explore_emotion_meaning()
            text = f"{question}\n" + "\n".join(options)
            await state.update_data(last_options=[opt[3:].strip() for opt in options])
            append_dialog_history(user_id, text, "assistant")
            await message.answer(text)
            return

        elif emotion_step == "cognitive_1":
            save_user_data(user_id, "emotion_step", "cognitive_2")
            blocks = reframe_thinking()
            question, options = blocks[1]
            text = f"{question}\n" + "\n".join(options)
            await state.update_data(last_options=[opt[3:].strip() for opt in options])
            append_dialog_history(user_id, text, "assistant")
            await message.answer(text)
            return

        elif emotion_step == "cognitive_2":
            save_user_data(user_id, "emotion_step", "done")
            blocks = reframe_thinking()
            question, options = blocks[2]
            text = f"{question}\n" + "\n".join(options)
            append_dialog_history(user_id, text, "assistant")
            await message.answer(text)
            return

        else:
            await state.set_state(DialogState.phase_4_solutions)
            save_user_data(user_id, "resource_step", "resources")
            topic = user_data.get("topic", "")
            history = [m["content"] for m in get_dialog_history(user_id) if m["role"] == "user"]
            questions = explore_resources(topic, history)
            question, options = questions[0]
            text = f"{question}\n" + "\n".join(options)
            await state.update_data(last_options=[opt[3:].strip() for opt in options])
            append_dialog_history(user_id, text, "assistant")
            await message.answer(text)
            return

    if phase == DialogState.phase_4_solutions:
        current_resource = user_data.get("resource_step", "resources")
        topic = user_data.get("topic", "")
        history = [m["content"] for m in get_dialog_history(user_id) if m["role"] == "user"]

        if current_resource == "resources":
            save_user_data(user_id, "resource_step", "plan_1")
            questions = explore_resources(topic, history)
            question, options = questions[0]
            text = f"{question}\n" + "\n".join(options)
            append_dialog_history(user_id, text, "assistant")
            await message.answer(text)
            return

        elif current_resource == "plan_1":
            save_user_data(user_id, "resource_step", "plan_2")
            questions = collaborative_planning(topic, history)
            question, options = questions[0]
            text = f"{question}\n" + "\n".join(options)
            await state.update_data(last_options=[opt[3:].strip() for opt in options])
            append_dialog_history(user_id, text, "assistant")
            await message.answer(text)
            return

        elif current_resource == "plan_2":
            await state.set_state(DialogState.phase_5_summary)
            questions = collaborative_planning(topic, history)
            question, options = questions[1]
            text = f"{question}\n" + "\n".join(options)
            await state.update_data(last_options=[opt[3:].strip() for opt in options])
            append_dialog_history(user_id, text, "assistant")
            await message.answer(text)
            return

    if phase == DialogState.phase_5_summary:
        topic = user_data.get("topic", "")
        history = [m["content"] for m in get_dialog_history(user_id)]
        question_block, support_lines = summarize_insights(topic, history)

        options = [line[3:].strip() for line in question_block.splitlines() if line.strip().startswith(("A)", "B)", "C)", "D)"))]
        if options:
            await state.update_data(last_options=options) 
        append_dialog_history(user_id, question_block, "assistant")
        await message.answer(question_block)

        await state.update_data(summary_support="\n".join(support_lines))
        await state.set_state(DialogState.summary_answer)
        return

    if current_state == DialogState.summary_answer.state:
        append_dialog_history(user_id, user_input, "user")
        topic = user_data.get("topic", "")
        history = [m["content"] for m in get_dialog_history(user_id) if m["role"] == "user"]
        data = await state.get_data()
        support_text = data.get("summary_support", "").replace('"', '').strip()

        summary = f"Главная тема: {topic}\n\nВыводы пользователя:\n" + "\n".join(history[-3:])
        save_user_data(user_id, "summary", summary)
        save_user_data(user_id, "profile", "done")
        
        final_message = f"{support_text}\n\nЕсли хочешь — можем просто поболтать дальше."
        append_dialog_history(user_id, final_message, "assistant")
        await message.answer(final_message)

        await state.set_state(DialogState.completed)
        generate_user_summary(user_id)
        return

    history = get_dialog_history(user_id)
    prompt = build_prompt(history, phase.state)
    response = generate_ai_response(prompt)
    append_dialog_history(user_id, response, "assistant")
    await message.answer(response)


def generate_unique_greeting(name: str) -> str:
    prompt = f"""
Ты — AI-помощница, подруга по переписке. К тебе обращается девушка по имени {name}, у которой может быть тревога, сомнения, тяжесть внутри.

Сгенерируй короткое (1–3 предложения) приветствие в стиле писательницы из Нью-Йорк Таймс.  
Обязательно вырази:
- готовность помочь без осуждения
- атмосферу тепла и принятия
- стиль — не как открытка, а как душевный разговор между близкими

Формат:
- До 250 символов
- Обращение на "ты"
- Без клише и пафоса
- Включи мягкое приглашение поделиться
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.85,
        max_tokens=150,
    )
    return response.choices[0].message.content.strip()


def generate_context_question() -> tuple[str, list[str]]:
    prompt = """
Ты — AI-наставница, подруга, которая помогает девушке разобраться в её чувствах. 
Твоя задача — мягко спросить, о чём она хочет поговорить.

Сгенерируй:
- один короткий, тёплый вопрос (1 строка, на "ты")
- 4 варианта ответа A–D (до 10 слов каждый), тоже на "ты", без формальностей

Варианты должны сохранять суть:
A — беспокойство  
B — ситуация  
C — потребность в поддержке  
D — свой вариант  

Формат:
Вопрос: [текст]
A) ...
B) ...
C) ...
D) ...
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.7,
        max_tokens=200,
    )
    lines = response.choices[0].message.content.strip().splitlines()
    question = lines[0].replace("Вопрос:", "").strip()
    options = lines[1:5]
    return question, options


def get_dialog_history(user_id: int) -> list:
    return get_user_data(user_id).get("history", [])


def generate_ai_response(prompt: str) -> str:
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.8,
        max_tokens=500,
    )
    return completion.choices[0].message.content.strip()
