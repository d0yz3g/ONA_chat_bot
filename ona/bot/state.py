from aiogram.fsm.state import State, StatesGroup

class DialogState(StatesGroup):
    ask_name = State()
    phase_1_init = State()
    phase_1_topic = State()  # добавлено для разделения фаз
    phase_2_listen = State()
    phase_3_emotions = State()
    phase_4_solutions = State()
    phase_5_summary = State()
    summary_answer = State()  # ← добавлено для обработки ответа после финального вопроса
    completed = State()
    crisis = State()

    confirm_restart = State()