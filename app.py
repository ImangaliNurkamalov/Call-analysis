import openai
import re
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from google.cloud import speech

app = Flask(__name__)

openai.api_key = 'API_KEY'

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

def format_text(text):
    lines = re.split(r'(\d+\.)', text)
    formatted_text = ''

    for i in range(1, len(lines), 2):
        formatted_text += f'{lines[i]}{lines[i + 1]}<br>'
    
    return formatted_text.strip()

@app.route('/')
def index():
    initial_analysis_result = ""
    return render_template('index.html', analysis_result = initial_analysis_result)

@app.route('/uploader', methods = ['GET', 'POST'])
def uploader_file():
   if request.method == 'POST':
      f = request.files['file']
      file_path = secure_filename(f.filename)
      f.save(file_path)

      converted_audio = convert_audio_to_text(file_path)
      analysis = analyze_text(converted_audio)
      ans = format_text(analysis)
      return render_template('index.html', analysis_result = ans)

@app.route('/analyze', methods=['POST'])
def analyze():
    analysis = analyze_text(prompt)
    ans = format_text(analysis)
    return render_template('index.html', analysis_result = ans)

if __name__ == '__main__':
    app.run(debug=True)
