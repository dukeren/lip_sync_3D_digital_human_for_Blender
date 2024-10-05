import librosa
import numpy as np
import bpy
import logging
import time  # Add this line to import the time module

logger = logging.getLogger("LipSyncLogger")
logger.setLevel(logging.DEBUG)

# 如果还没有处理器，添加一个控制台处理器
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# 英文音素到口型映射
ENGLISH_PHONEME_TO_VISEME = {
    'a': 'A', 'i': 'I', 'u': 'U', 'e': 'E', 'o': 'O',
    'm': 'U', 'b': 'U', 'p': 'U', 'f': 'U', 'v': 'U',
    's': 'I', 'z': 'I', 'th': 'I', 'ch': 'I', 'sh': 'I',
    'j': 'I', 'zh': 'I', 'l': 'I', 'r': 'I', 'y': 'I',
    'w': 'U', 'ng': 'E', 'h': 'A', 'k': 'E', 'g': 'E',
}

# 中文音素到口型映射
CHINESE_PHONEME_TO_VISEME = {
    'a': 'A', 'i': 'I', 'u': 'U', 'e': 'E', 'o': 'O', 'ü': 'I',
    'b': 'U', 'p': 'U', 'm': 'U', 'f': 'U',
    'd': 'I', 't': 'I', 'n': 'I', 'l': 'I',
    'g': 'E', 'k': 'E', 'h': 'E',
    'j': 'I', 'q': 'I', 'x': 'I',
    'z': 'I', 'c': 'I', 's': 'I',
    'zh': 'I', 'ch': 'I', 'sh': 'I', 'r': 'I',
    'y': 'U', 'w': 'U',
    'ai': 'A', 'ei': 'A', 'ao': 'O', 'ou': 'O',
    'an': 'E', 'en': 'E', 'in': 'E', 'un': 'E', 'ün': 'E',
    'ang': 'E', 'eng': 'E', 'ing': 'E', 'ong': 'E'
}

class LipSyncCore:
    def __init__(self, frame_rate=24.0, silence_threshold=0.01, max_silence_frames=5, language='chinese'):
        self.frame_rate = frame_rate
        self.silence_threshold = silence_threshold
        self.max_silence_frames = max_silence_frames
        self.set_language(language)
        logger.debug(f"LipSyncCore 初始化: frame_rate={frame_rate}, silence_threshold={silence_threshold}, max_silence_frames={max_silence_frames}, language={language}")

    def set_language(self, language):
        if language.lower() == 'english':
            self.phoneme_to_viseme = ENGLISH_PHONEME_TO_VISEME
        elif language.lower() == 'chinese':
            self.phoneme_to_viseme = CHINESE_PHONEME_TO_VISEME
        else:
            raise ValueError("Unsupported language. Choose 'english' or 'chinese'.")
        logger.info(f"设置语言为: {language}")

    def analyze_audio(self, audio_file):
        logger.info(f"开始分析音频文件: {audio_file}")
        y, sr = librosa.load(audio_file)
        duration = librosa.get_duration(y=y, sr=sr)
        logger.info(f"音频已加载. 采样率: {sr}, 音频时长: {duration} 秒")

        total_frames = int(duration * self.frame_rate)
        logger.debug(f"总帧数: {total_frames}")

        mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=10, hop_length=int(sr/self.frame_rate))
        chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=int(sr/self.frame_rate))
        logger.debug(f"生成 Mel 频谱图和色度图. Mel 频谱图形状: {mel_spec.shape}, 色度图形状: {chroma.shape}")

        visemes = self.generate_visemes(total_frames, mel_spec, chroma)
        logger.info(f"生成了 {len(visemes)} 个口型数据点")
        return visemes

    def generate_visemes(self, total_frames, mel_spec, chroma):
        logger.debug("开始生成口型序列")
        visemes = []
        silence_counter = 0
        current_viseme = None

        for frame in range(total_frames):
            time = frame / self.frame_rate
            frame_energy = np.sum(mel_spec[:, frame])

            if frame_energy > self.silence_threshold:
                pitch_frame = np.argmax(mel_spec[:, frame])
                chroma_frame = np.argmax(chroma[:, frame])
                phoneme_index = (pitch_frame + chroma_frame) % len(self.phoneme_to_viseme)
                current_phoneme = list(self.phoneme_to_viseme.keys())[phoneme_index]
                current_viseme = self.phoneme_to_viseme[current_phoneme]
                silence_counter = 0
            elif silence_counter >= self.max_silence_frames:
                current_viseme = None
            else:
                silence_counter += 1

            viseme_strength = min(1.0, frame_energy / self.silence_threshold) if current_viseme else 0.0
            visemes.append((frame, current_viseme, viseme_strength))
            if frame % 100 == 0:  # 每100帧打印一次，避免日志过多
                logger.debug(f"帧 {frame}: 时间 {time:.2f}s, 口型 {current_viseme}, 强度 {viseme_strength:.2f}, 能量 {frame_energy:.4f}, 静音计数 {silence_counter}")

        logger.debug("口型序列生成完成")
        return visemes

    def apply_visemes_to_mesh(self, obj, visemes, action_name):
        logger.info(f"开始将口型应用到网格, 对象: {obj.name}, 动作名称: {action_name}")
        if not obj.data.shape_keys:
            sk_basis = obj.shape_key_add(name='Basis')
            obj.data.shape_keys.use_relative = True
            logger.info("创建了'Basis'形态键")

        shape_keys = obj.data.shape_keys.key_blocks
        for viseme in ['A', 'I', 'U', 'E', 'O']:
            if viseme not in shape_keys:
                obj.shape_key_add(name=viseme)
                logger.info(f"创建了形态键: {viseme}")

        lip_sync_action = bpy.data.actions.new(name=action_name)
        if not obj.data.shape_keys.animation_data:
            obj.data.shape_keys.animation_data_create()
        obj.data.shape_keys.animation_data.action = lip_sync_action
        logger.debug(f"创建了新的动作: {action_name}")

        for frame, viseme, strength in visemes:
            for shape_key in shape_keys:
                if shape_key.name in ['A', 'I', 'U', 'E', 'O']:
                    shape_key.value = strength if shape_key.name == viseme else 0.0
                    shape_key.keyframe_insert("value", frame=frame)

        logger.info("完成将口型应用到网格")
        return lip_sync_action

    def create_nla_track(self, obj, action, track_name, strip_name):
        logger.info(f"开始创建NLA轨道, 对象: {obj.name}, 轨道名称: {track_name}, 条带名称: {strip_name}")
        if not obj.animation_data:
            obj.animation_data_create()
        
        nla_tracks = obj.animation_data.nla_tracks
        
        lip_sync_track = nla_tracks.new()
        lip_sync_track.name = track_name
        logger.debug(f"创建了新的NLA轨道: {track_name}")
        
        lip_sync_strip = lip_sync_track.strips.new(strip_name, start=1, action=action)
        lip_sync_strip.blend_type = 'REPLACE'
        lip_sync_strip.use_auto_blend = False
        lip_sync_strip.influence = 1.0
        logger.debug(f"在轨道 {track_name} 上创建了新的条带: {strip_name}")
        
        logger.info("完成NLA轨道创建")

    def process_audio_and_apply_lipsync(self, obj, audio_file):
        logger.info(f"开始处理音频和应用唇形同步, 对象: {obj.name}, 音频文件: {audio_file}")
        try:
            timestamp = int(time.time())
            action_name = f"LipSyncAction_{timestamp}"
            track_name = f"LipSync_{timestamp}"
            strip_name = f"LipSync_{timestamp}"

            visemes = self.analyze_audio(audio_file)
            action = self.apply_visemes_to_mesh(obj, visemes, action_name)
            self.create_nla_track(obj, action, track_name, strip_name)
            logger.info("完成音频处理和唇形同步应用")
        except Exception as e:
            logger.error(f"处理音频和应用唇形同步时发生错误: {str(e)}")
            raise