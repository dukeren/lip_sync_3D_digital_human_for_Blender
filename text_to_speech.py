import logging
import requests
import os
import json

class TextToSpeech:
    def __init__(self, method="ChatTTS"):
        self.method = method
        self.config = self._load_config()

    def _load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'r') as f:
            return json.load(f)

    def synthesize(self, text):
        if self.method == "ChatTTS":
            return self._synthesize_chattts(text)
        else:
            raise ValueError(f"Unsupported text to speech method: {self.method}")

    def _synthesize_chattts(self, text):
        logging.info("使用ChatTTS进行文本到语音转换")
        try:
            form_data = {
                'text': text,
                'prompt': "[break_6]",
                'voice': "1031.pt",
                'speed': '5',
                'temperature': '0.1',
                'top_p': '0.701',
                'top_k': '20',
                'refine_max_new_token': '384',
                'infer_max_new_token': '2048',
                'text_seed': '42',
                'skip_refine': '1',
                'is_stream': '0',
                'custom_voice': '0'
            }
            
            tts_response = requests.post(
                self.config['chattts']['url'],
                data=form_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if tts_response.status_code == 200:
                tts_data = tts_response.json()
                if tts_data['code'] == 0:
                    voice_dir = os.path.join(os.path.dirname(__file__), "Voice")
                    os.makedirs(voice_dir, exist_ok=True)
                    
                    audio_files = []
                    for audio_file in tts_data['audio_files']:
                        url = audio_file['url']
                        filename = os.path.basename(url)
                        file_path = os.path.join(voice_dir, filename)
                        
                        response = requests.get(url)
                        if response.status_code == 200:
                            with open(file_path, 'wb') as f:
                                f.write(response.content)
                            logging.info(f"音频文件已下载到: {file_path}")
                            audio_files.append(file_path)
                        else:
                            logging.error(f"下载音频文件失败: {url}")
                    
                    return audio_files
                else:
                    logging.error(f"TTS处理错误: {tts_data['msg']}")
            else:
                logging.error(f"TTS API调用错误: {tts_response.text}")
        except Exception as e:
            logging.error(f"文本到语音处理错误: {str(e)}")
        
        return None