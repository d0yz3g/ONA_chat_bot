import os
import tempfile
from openai import OpenAI

# ⬇️ ДО ИМПОРТА pydub добавляем путь к ffmpeg в PATH
os.environ["PATH"] += r";C:\ffmpeg\ffmpeg-7.1.1-essentials_build\bin"

from pydub import AudioSegment
from ona.bot.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def convert_ogg_to_mp3(ogg_bytes: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as in_file:
        in_file.write(ogg_bytes)
        in_file_path = in_file.name

    audio = AudioSegment.from_file(in_file_path, format="ogg")
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as out_file:
        audio.export(out_file.name, format="mp3")
        return out_file.name

async def transcribe_voice(voice_bytes: bytes) -> str:
    mp3_path = convert_ogg_to_mp3(voice_bytes)

    with open(mp3_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="text"
        )

    return transcription.strip()
