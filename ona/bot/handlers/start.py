from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.methods import SendChatAction

from ona.bot.state import DialogState
from ona.bot.supabase_service import get_user_data, save_user_data
from ona.bot.dialog_manager import generate_unique_greeting
from ona.bot.utils.security import sanitize_user_input

router = Router()

@router.message(F.text == "/start")
async def start_dialog(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)

    await state.clear()

    if user_data and user_data.get("profile") == "done" and user_data.get("summary"):
        await state.set_state(DialogState.confirm_restart)
        await message.answer(
            "Мы уже хорошо поработали вместе раньше.\n"
            "Хочешь начать всё сначала или продолжим разговор?"
        )
        return

    # Иначе — первый запуск, всё обнуляем
    save_user_data(user_id, "history", [])
    save_user_data(user_id, "summary", "")
    save_user_data(user_id, "topic", "")
    save_user_data(user_id, "name", "")
    save_user_data(user_id, "profile", "")

    await state.set_state(DialogState.ask_name)
    await message.bot(SendChatAction(chat_id=message.chat.id, action="typing"))
    greeting = generate_unique_greeting("друг")
    await message.answer(f"{greeting}\n\nКак тебя зовут, чтобы я могла обращаться по имени?")

@router.message(DialogState.confirm_restart)
async def handle_restart_confirmation(message: Message, state: FSMContext):
    user_id = message.from_user.id
    answer = sanitize_user_input(message.text.lower())

    if answer in ["да", "хочу", "давай", "начать сначала", "сначала", "yes"]:
        await state.clear()
        save_user_data(user_id, "history", [])
        save_user_data(user_id, "summary", "")
        save_user_data(user_id, "topic", "")
        save_user_data(user_id, "name", "")
        save_user_data(user_id, "profile", "")

        await state.set_state(DialogState.ask_name)
        await message.bot(SendChatAction(chat_id=message.chat.id, action="typing"))
        greeting = generate_unique_greeting("друг")
        await message.answer(f"{greeting}\n\nКак тебя зовут, чтобы я могла обращаться по имени?")
    else:
        # Продолжить общение с уже сформированным профилем
        await state.set_state(DialogState.completed)
        user_data = get_user_data(user_id)
        name = user_data.get("name", "дорогая")
        greeting = generate_unique_greeting(name)
        await message.answer(f"{greeting}\nЕсли хочешь — можем просто поболтать дальше.")
