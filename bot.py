import requests
import json
import os
import subprocess
import urllib.request
import time
import speech_recognition as sr

# Токен бота
TOKEN = "7650238725:AAEhe_SeEeNnAuh45YxpnjRvW1MjGwIo-MI"
# Путь к ffmpeg
FFMPEG_PATH = "/usr/bin/ffmpeg"
# URL для Telegram API
BASE_URL = f"https://api.telegram.org/bot{TOKEN}/"

# Форматируем текст транскрипции
def format_transcription(text):
    if not text:
        return text
    # Делаем первую букву заглавной
    return text[0].upper() + text[1:] if len(text) > 1 else text.upper()

# Получаем обновления
def get_updates(offset=None):
    url = BASE_URL + "getUpdates"
    params = {"timeout": 100, "offset": offset}
    try:
        response = requests.get(url, params=params)
        return response.json()
    except:
        return {"ok": False}

# Отправляем сообщение
def send_message(chat_id, text, reply_to_message_id=None, parse_mode=None):
    url = BASE_URL + "sendMessage"
    params = {"chat_id": chat_id, "text": text}
    if reply_to_message_id:
        params["reply_to_message_id"] = reply_to_message_id
    if parse_mode:
        params["parse_mode"] = parse_mode
    try:
        response = requests.get(url, params=params)
        return response.json()
    except:
        return None

# Скачиваем файл
def download_file(file_url, file_name):
    try:
        urllib.request.urlretrieve(file_url, file_name)
    except:
        raise

# Конвертируем ogg в wav
def convert_ogg_to_wav(ogg_file, wav_file):
    command = [FFMPEG_PATH, "-i", ogg_file, wav_file, "-y"]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise Exception("Ошибка конвертации")

# Транскрибируем аудио
def transcribe_audio(wav_file):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(wav_file) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language="ru-RU")
            return format_transcription(text)
    except sr.UnknownValueError:
        return "Не удалось распознать речь"
    except sr.RequestError:
        return "Ошибка сервиса распознавания"
    except:
        return "Ошибка транскрипции"

def main():
    last_update_id = None
    print("Бот запущен...")
    
    while True:
        updates = get_updates(last_update_id)
        if not updates.get("ok"):
            time.sleep(1)
            continue
        
        for update in updates.get("result", []):
            last_update_id = update["update_id"] + 1
            if "message" not in update:
                continue
            
            chat_id = update["message"]["chat"]["id"]
            message = update["message"]
            
            if "text" in message and message["text"].startswith("/пиздабол"):
                if "reply_to_message" in message and "voice" in message["reply_to_message"]:
                    try:
                        # Сообщаем, что начали расшифровку
                        send_message(chat_id, "Ща посмотрим о чём он пиздит...", message["message_id"])
                        
                        # Получаем file_id голосового
                        file_id = message["reply_to_message"]["voice"]["file_id"]
                        # Запрашиваем file_path
                        file_info = requests.get(BASE_URL + f"getFile?file_id={file_id}").json()
                        if not file_info.get("ok"):
                            send_message(chat_id, "Ошибка получения файла.", message["message_id"])
                            continue
                        
                        file_path = file_info["result"]["file_path"]
                        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
                        download_file(file_url, "voice.ogg")
                        convert_ogg_to_wav("voice.ogg", "voice.wav")
                        text = transcribe_audio("voice.wav")
                        # Отправляем с жирным "Ого напиздел!:"
                        send_message(chat_id, f"<b>Ого напиздел!:</b> {text}", message["message_id"], parse_mode="HTML")
                        if os.path.exists("voice.ogg"):
                            os.remove("voice.ogg")
                        if os.path.exists("voice.wav"):
                            os.remove("voice.wav")
                    except Exception as e:
                        send_message(chat_id, f"Ошибка: {str(e)}", message["message_id"])
                else:
                    send_message(chat_id, "Ответьте на голосовое сообщение с /пиздабол.", message["message_id"])
        
        time.sleep(1)

if __name__ == "__main__":
    main()