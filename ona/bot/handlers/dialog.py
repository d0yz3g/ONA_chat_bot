from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from ona.bot.state import DialogState
from ona.bot.dialog_manager import process_message
from ona.bot.utils.security import sanitize_user_input
from ona.bot.utils.redis_service import RedisRateLimiter
from ona.bot.utils.voice_processing import transcribe_voice  # ✅ новое

router = Router()
rate_limiter = RedisRateLimiter()

# ✅ Поддержка латиницы и кириллицы
OPTION_MAPPING = {
    "a": 0, "а": 0,
    "b": 1, "б": 1,
    "c": 2, "в": 2,
    "d": 3, "г": 3,
}

@router.message(F.voice | F.text)
async def handle_user_message(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if not await rate_limiter.is_allowed(user_id, limit=1, window=6):
        await message.answer("⏳ Подожди немного перед следующим сообщением.")
        return

    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Давай начнём с команды /start 💬")
        return

    # ✅ Голосовое сообщение
    if message.voice:
        file = await message.bot.get_file(message.voice.file_id)
        voice_bytes = await message.bot.download_file(file.file_path)
        user_input = await transcribe_voice(voice_bytes.read())
    else:
        user_input = message.text.strip()

    # ✅ Обработка выбора A–D
    data = await state.get_data()
    if "last_options" in data and message.text:
        key = user_input.lower()
        idx_map = {"a": 0, "а": 0, "b": 1, "б": 1, "c": 2, "в": 2, "d": 3, "г": 3}
        if key in idx_map:
            idx = idx_map[key]
            options = data["last_options"]
            if 0 <= idx < len(options):
                user_input = options[idx]

    await process_message(message, state, user_input)
