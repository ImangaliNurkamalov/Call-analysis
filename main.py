from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext
import asyncio
import logging
import requests
import openai
import re
from werkzeug.utils import secure_filename
from google.cloud import speech
import os
import time

BOT_TOKEN = 'TOKEN'

openai.api_key = 'API_KEY'

folder_path = "foler_path"

prompt = """Сделай пожалуйста: 

Саммари диалога
пример: - Клиент, по имени Евгений Петрович, интересуется покупкой квартиры в 14-ом доме, первый корпус, на улице Ключникова в Воронеже...

Ошибки и решения
пример: - Менеджер не уточнил бюджет клиента и не провел квалификацию на этапе начала разговора...

Общая оценка работы менеджера по скрипту
пример: -В целом, менеджер выполненный большую часть шагов с умением. Однако, иногда он мог бы использовать более понятные термины и более чётко объяснять...

Возражения клиента
пример: - Клиент считает цены на квартиры дорогими.
"""

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Welcome to the Bult Bot!\nUse /start to start again\nUse /upload to upload the audio file\nUse /analyze to analyze the bot')

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Works!')


def convert_audio_to_text(file_name):
    client = speech.SpeechClient.from_service_account_file('key.json')

    with open(file_name, 'rb') as f:
        mp3_data = f.read()

    audio_file = speech.RecognitionAudio(content=mp3_data)

    config = speech.RecognitionConfig(
        sample_rate_hertz = 44100,
        enable_automatic_punctuation = True,
        language_code = 'ru-RU'
    )

    response = client.recognize(
        config=config,
        audio=audio_file
    )

    for result in response.results:
        return result.alternatives[0].transcript

def analyze_text(cont):
    completion = openai.ChatCompletion.create(
        model = 'gpt-3.5-turbo',
        messages = [
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": cont
            }
        ],
        temperature = 0
    )
    return completion['choices'][0]['message']['content']


async def downloader(update, context):
    # Download file
    fileName = update.message.document.file_name
    new_file = await update.message.effective_attachment.get_file()
    await new_file.download_to_drive(fileName)

    # Acknowledge file received
    await update.message.reply_text(f"{fileName} saved successfully")

    # Send the file
    print("\n------------------------------------------------")
    converted_audio = convert_audio_to_text(fileName)
    analysis = analyze_text(converted_audio)
    await update.message.reply_text(f"{analysis}")
    await update.message.reply_text(f"Here is transcript: {converted_audio}")
    #print(analyze_text(converted_audio))

    #chat_id = update.message.chat.id
    #file_id = '20221222-.pptx'
    #await context.bot.send_document(chat_id=chat_id, document=file_id)

if __name__ == '__main__':
    print("Starting the bot...")
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('custom', custom_command))
    app.add_handler(MessageHandler(filters.ALL, downloader))

    print("Polling...")
    app.run_polling(poll_interval=3)