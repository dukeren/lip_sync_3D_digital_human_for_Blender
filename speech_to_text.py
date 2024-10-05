import logging
import requests
import json
import os

class SpeechToText:
    def __init__(self, method="Whisper"):
        self.method = method
        self.config = self._load_config()

    def _load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'r') as f:
            return json.load(f)

    def transcribe(self, file_name):
        if self.method == "Whisper":
            return self._transcribe_whisper(file_name)
        elif self.method == "Other":
            return self._transcribe_other(file_name)
        else:
            raise ValueError(f"Unsupported speech to text method: {self.method}")

    def _transcribe_whisper(self, file_name):
        logging.info("Using Whisper to process audio")
        try:
            with open(file_name, 'rb') as audio_file:
                files = {'audio_file': audio_file}
                response = requests.post(f"{self.config['whisper']['url']}?output=json", files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    transcribed_text = result['text']
                    logging.info(f"Transcribed text: {transcribed_text}")
                    return transcribed_text
                else:
                    logging.error(f"Error in Whisper ASR request: {response.text}")
                    return None
        except Exception as e:
            logging.error(f"Error processing audio with Whisper: {str(e)}")
            return None

    def _transcribe_other(self, file_name):
        logging.info("Using Xiaodu to process audio")
        # 实现Xiaodu的转录逻辑
        # 这里需要根据Xiaodu的API来实现
        return None