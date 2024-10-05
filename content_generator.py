import logging
import openai
import requests
import json
import subprocess
import os

class ContentGenerator:
    def __init__(self, default_method="Ollama"):
        self.default_method = default_method
        self.config = self._load_config()

    def _load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'r') as f:
            return json.load(f)

    def generate(self, text, method=None):
        method = method or self.default_method
        if method == "OpenAI":
            return self._generate_openai(text)
        elif method == "Ollama":
            return self._generate_ollama(text)
        elif method == "Dify":
            return self._generate_dify(text)
        else:
            raise ValueError(f"Unsupported content generation method: {method}")

    def _generate_openai(self, text):
        logging.info("使用OpenAI生成内容")
        try:
            openai.api_key = self.config['openai']['api_key']
            response = openai.Completion.create(
                engine="text-davinci-002",
                prompt=text,
                max_tokens=100
            )
            generated_content = response.choices[0].text.strip()
            logging.info(f"生成的内容: {generated_content}")
            return generated_content
        except Exception as e:
            logging.error(f"使用OpenAI生成内容时出错: {str(e)}")
            return None

    def _generate_ollama(self, text):
        logging.info("使用Ollama生成内容")
        try:
            response = requests.post(
                self.config['ollama']['url'], 
                json={'model': self.config['ollama']['model'], 'prompt': text},
                stream=True
            )
            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        json_response = json.loads(line)
                        if 'response' in json_response:
                            full_response += json_response['response']
                        if json_response.get('done', False):
                            break
                logging.info(f"生成的内容: {full_response}")
                return full_response
            else:
                logging.error(f"使用Ollama生成内容时出错: {response.text}")
                return None
        except Exception as e:
            logging.error(f"使用Ollama生成内容时出错: {str(e)}")
            return None

    def _generate_dify(self, text):
        logging.info("使用Dify Agent生成内容")
        url = self.config['dify']['url']
        api_key = self.config['dify']['api_key']
        
        data = {
            "query": text,
            "user": "user123",
            "inputs": {},
            "response_mode": "streaming"
        }
        
        curl_command = [
            'curl', '-X', 'POST', url,
            '-H', 'Content-Type: application/json',
            '-H', f'Authorization: Bearer {api_key}',
            '-d', json.dumps(data)
        ]
        
        try:
            result = subprocess.run(curl_command, capture_output=True, text=True)
            logging.debug(f"Curl command output: {result.stdout}")
            logging.debug(f"Curl command error: {result.stderr}")
            
            if result.returncode == 0:
                response_lines = result.stdout.split('\n')
                full_response = ""
                for line in response_lines:
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if data['event'] == 'agent_message':
                                full_response += data['answer']
                        except json.JSONDecodeError:
                            logging.warning(f"无法解析JSON: {line}")
                
                logging.info(f"生成的内容: {full_response}")
                return full_response
            else:
                logging.error(f"使用Dify Agent生成内容时出错: {result.stderr}")
                return None
        except Exception as e:
            logging.error(f"执行curl命令时出错: {str(e)}")
            return None