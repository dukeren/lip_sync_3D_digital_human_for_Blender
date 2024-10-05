import os
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
import cgi
import socket
import html
from urllib.parse import parse_qs
import threading

class FileHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, callback=None, **kwargs):
        self.callback = callback
        super().__init__(*args, **kwargs)

    def do_POST(self):
        logging.info("Received POST request")
        content_type = self.headers['Content-Type']
        logging.debug(f"Content-Type: {content_type}")
        
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()

        try:
            if 'multipart/form-data' in content_type:
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST',
                            'CONTENT_TYPE': self.headers['Content-Type']}
                )
                
                logging.debug(f"Form keys: {list(form.keys())}")
                
                if 'audio' in form:
                    audio_item = form['audio']
                    if audio_item.filename:
                        file_name = os.path.basename(audio_item.filename)
                        file_content = audio_item.file.read()
                        
                        with open(file_name, 'wb') as f:
                            f.write(file_content)
                        
                        logging.info(f"Received audio file: {file_name}")
                        print(f"Received audio file: {file_name}")
                        result = {'type': 'audio', 'filename': file_name}
                    else:
                        logging.warning("Audio field is present but no file was uploaded")
                elif 'text' in form:
                    text = form['text'].value
                    logging.info(f"Received text: {text}")
                    print(f"Received text: {text}")
                    result = {'type': 'text', 'content': text}
                else:
                    logging.warning(f"No 'audio' or 'text' field in form data. Available fields: {list(form.keys())}")
            else:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                logging.debug(f"POST data: {post_data}")
                
                form_data = parse_qs(post_data)
                if 'text' in form_data:
                    text = form_data['text'][0]
                    logging.info(f"Received text: {text}")
                    print(f"Received text: {text}")
                    result = {'type': 'text', 'content': text}
                else:
                    logging.warning("No 'text' field in form data")

            self.wfile.write('请求处理成功'.encode('utf-8'))

            if self.callback and result:
                self.callback(result)

            return None
        except Exception as e:
            logging.error(f"Error processing request: {str(e)}")
            logging.error(f"Error type: {type(e).__name__}")
            logging.error(f"Error details: {e.args}")
            self.send_error(500, f"Internal server error: {str(e)}".encode('utf-8'))
            return None

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type")
        self.end_headers()

    def send_error(self, code, message=None, explain=None):
        try:
            short, long = self.responses[code]
        except KeyError:
            short, long = '???', '???'
        if message is None:
            message = short
        if explain is None:
            explain = long
        self.log_error("code %d, message %s", code, message)
        self.send_response(code, message)
        self.send_header('Connection', 'close')
        self.send_header('Content-Type', 'text/html;charset=utf-8')
        self.end_headers()

        content = (self.error_message_format % {
            'code': code,
            'message': html.escape(message, quote=False),
            'explain': html.escape(explain, quote=False)
        })
        body = content.encode('UTF-8', 'replace')
        self.wfile.write(body)

class FileHandlerServer:
    def __init__(self, port=9990, callback=None):
        self.port = port
        self.server = None
        self.server_thread = None
        self.stop_event = None
        self.callback = callback

    def start(self):
        if self.server is None:
            try:
                self.stop_event = threading.Event()
                handler = lambda *args: FileHandler(*args, callback=self.callback)
                self.server = HTTPServer(("localhost", self.port), handler)
                self.server_thread = threading.Thread(target=self.run_server)
                self.server_thread.start()
                logging.info("Server started successfully")
                return True
            except OSError:
                logging.error("Failed to start server. Port might be in use.")
                return False
        return True

    def run_server(self):
        logging.info("Server is running")
        while self.stop_event and not self.stop_event.is_set():
            self.server.handle_request()

    def stop(self):
        if self.server:
            logging.info("Stopping server...")
            self.stop_event.set()
            try:
                with socket.create_connection(("localhost", self.port), timeout=1):
                    pass
            except:
                logging.warning("Failed to send dummy request to unblock server")
            self.server.server_close()
            self.server = None
            self.server_thread = None
            self.stop_event = None
            logging.info("Server stopped")

    def is_running(self):
        return self.server is not None and self.server_thread is not None and self.server_thread.is_alive()