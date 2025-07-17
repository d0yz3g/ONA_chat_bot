import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

# Получаем ключ шифрования из .env
fernet_key = os.getenv("FERNET_KEY")
cipher_suite = Fernet(fernet_key.encode())

def decrypt_key(encrypted_key: str) -> str:
    if not encrypted_key:
        raise ValueError("Зашифрованный ключ не найден в переменных окружения")
    return cipher_suite.decrypt(encrypted_key.encode()).decode()

# Расшифровываем ключи из .env (заполни .env зашифрованными значениями, как будет дальше показано)
TELEGRAM_TOKEN = decrypt_key(os.getenv("TELEGRAM_TOKEN_ENC"))
OPENAI_API_KEY = decrypt_key(os.getenv("OPENAI_API_KEY_ENC"))
SUPABASE_URL = decrypt_key(os.getenv("SUPABASE_URL_ENC"))
SUPABASE_KEY = decrypt_key(os.getenv("SUPABASE_KEY_ENC"))

# Общие параметры
DEFAULT_EMOTION_STYLE = {
    "тон": "дружеский, теплый",
    "обращение": "на ты",
    "позиция": "подруга",
    "род": "женский",
    "фокус": "на человеке, а не на проблеме"
}
