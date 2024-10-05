import bpy
import logging
import threading
from bpy_extras.io_utils import ImportHelper
from .file_handler import FileHandlerServer
from .speech_to_text import SpeechToText
from .content_generator import ContentGenerator
from .text_to_speech import TextToSpeech

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ContentManager:
    def __init__(self):
        self.file_handler = None
        self.speech_to_text = SpeechToText("Whisper")
        self.content_generator = ContentGenerator("Ollama")
        self.text_to_speech = TextToSpeech("ChatTTS")
        self.processing_thread = None

    def start_listening(self, port):
        if self.file_handler:
            self.stop_listening()
        self.file_handler = FileHandlerServer(callback=self.handle_input, port=port)
        return self.file_handler.start()

    def stop_listening(self):
        if self.file_handler:
            self.file_handler.stop()
            self.file_handler = None

    def is_listening(self):
        return self.file_handler is not None and self.file_handler.is_running()

    def handle_input(self, input_data):
        logging.info(f"Received input: {input_data}")
        self.process_input(input_data)

    def process_input(self, input_data):
        if input_data['type'] == 'audio':
            text = self.speech_to_text.transcribe(input_data['filename'])
        elif input_data['type'] == 'text':
            text = input_data['content']
        else:
            logging.error(f"Unsupported input type: {input_data['type']}")
            return

        if text:
            current_method = bpy.context.scene.content_generation
            generated_content = self.content_generator.generate(text, current_method)
            if generated_content:
                self.generate_speech(generated_content)
            else:
                logging.error("未能生成内容")
        else:
            logging.error("未能获取文本")

    def generate_speech(self, text):
        audio_files = self.text_to_speech.synthesize(text)
        if audio_files:
            logging.info(f"生成的音频文件: {audio_files}")
        else:
            logging.error("未能生成音频文件")
            bpy.app.timers.register(lambda: self.show_error_message("未能生成音频文件"))

    def process_text_file(self, filepath):
        def process_in_background():
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    text = file.read()
                self.generate_speech(text)
                bpy.app.timers.register(self.update_ui)
            except Exception as e:
                logging.error(f"处理文本文件时出错: {str(e)}")
                bpy.app.timers.register(lambda: self.show_error_message(str(e)))

        self.processing_thread = threading.Thread(target=process_in_background)
        self.processing_thread.start()

    def update_ui(self):
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

    def show_success_message(self, message):
        def draw(self, context):
            self.layout.label(text=message)
        bpy.context.window_manager.popup_menu(draw, title="处理成功", icon='INFO')

    def show_error_message(self, message):
        def draw(self, context):
            self.layout.label(text=message)
        bpy.context.window_manager.popup_menu(draw, title="处理错误", icon='ERROR')

    def update_speech_to_text(self, method):
        self.speech_to_text = SpeechToText(method)

    def update_content_generation_method(self, method):
        self.content_generator = ContentGenerator(method)

    def update_text_to_speech(self, method):
        self.text_to_speech = TextToSpeech(method)

content_manager = ContentManager()

class CONTENT_PT_panel(bpy.types.Panel):
    bl_label = "Content Generation"
    bl_idname = "CONTENT_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "input_method")

        if scene.input_method == 'LISTEN':
            layout.prop(scene, "listening_port")
            if content_manager.is_listening():
                layout.operator("content.toggle_listening", text="停止监听")
            else:
                layout.operator("content.toggle_listening", text="开始监听")
        else:
            layout.operator("content.select_and_process_text_file", text="Select and Process Text File")

        layout.prop(scene, "speech_to_text")
        layout.prop(scene, "content_generation")
        layout.prop(scene, "text_to_speech")

class CONTENT_OT_toggle_listening(bpy.types.Operator):
    bl_idname = "content.toggle_listening"
    bl_label = "Toggle Listening"

    def execute(self, context):
        scene = context.scene
        if not content_manager.is_listening():
            if content_manager.start_listening(scene.listening_port):
                scene.is_listening = True
        else:
            content_manager.stop_listening()
            scene.is_listening = False
        return {'FINISHED'}

class CONTENT_OT_select_and_process_text_file(bpy.types.Operator, ImportHelper):
    bl_idname = "content.select_and_process_text_file"
    bl_label = "Select and Process Text File"
    
    filter_glob: bpy.props.StringProperty(
        default='*.txt',
        options={'HIDDEN'}
    )

    def execute(self, context):
        if self.filepath:
            content_manager.process_text_file(self.filepath)
            self.report({'INFO'}, f"开始处理文件: {self.filepath}")
        else:
            self.report({'ERROR'}, "未选择文件")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(CONTENT_PT_panel)
    bpy.utils.register_class(CONTENT_OT_toggle_listening)
    bpy.utils.register_class(CONTENT_OT_select_and_process_text_file)

    bpy.types.Scene.input_method = bpy.props.EnumProperty(
        items=[
            ('LISTEN', "Listen on Port", "Listen for input on a specific port"),
            ('FILE', "Select File", "Select and process a text file"),
        ],
        name="输入类型",
        default='LISTEN'
    )

    bpy.types.Scene.listening_port = bpy.props.IntProperty(
        name="监听端口",
        default=9990,
        min=1024,
        max=65535
    )

    bpy.types.Scene.is_listening = bpy.props.BoolProperty(
        name="Is Listening",
        default=False
    )

    bpy.types.Scene.speech_to_text = bpy.props.EnumProperty(
        items=[
            ("Whisper", "Whisper", ""),
            ("Other", "Other Voice Assistant", "")
        ],
        name="语音转文本",
        default="Whisper",
        update=lambda self, context: content_manager.update_speech_to_text(self.speech_to_text)
    )

    bpy.types.Scene.content_generation = bpy.props.EnumProperty(
        items=[
            ("OpenAI", "OpenAI", ""),
            ("Ollama", "Ollama", ""),
            ("Dify", "Dify", "")
        ],
        name="文本生成",
        default="Ollama",
        update=lambda self, context: content_manager.update_content_generation_method(self.content_generation)
    )

    bpy.types.Scene.text_to_speech = bpy.props.EnumProperty(
        items=[
            ("ChatTTS", "ChatTTS", ""),
            ("Other", "Other", "")
        ],
        name="文本转语音",
        default="ChatTTS",
        update=lambda self, context: content_manager.update_text_to_speech(self.text_to_speech)
    )

def unregister():
    bpy.utils.unregister_class(CONTENT_PT_panel)
    bpy.utils.unregister_class(CONTENT_OT_toggle_listening)
    bpy.utils.unregister_class(CONTENT_OT_select_and_process_text_file)

    del bpy.types.Scene.input_method
    del bpy.types.Scene.is_listening
    del bpy.types.Scene.listening_port
    del bpy.types.Scene.speech_to_text
    del bpy.types.Scene.content_generation
    del bpy.types.Scene.text_to_speech

    content_manager.stop_listening()

if __name__ == "__main__":
    register()