import bpy
from collections import deque
from .logger import get_logger
import time

class LipSyncAnimationHandler:
    LIPSYNC_PREFIX = "LipSync"
    EXTRA_FRAMES = 10
    MAX_FRAME = 100000

    def __init__(self, scene):
        self.scene = scene
        self.logger = get_logger()
        self.animation_queue = deque()
        self.current_animation_end_frame = self.scene.frame_start

    def mark_lipsync_animation(self):
        obj = self.scene.lipsync_object
        if not obj:
            return

        self.scene.lipsync_last_modified = time.time()
        
        self.scene.lipsync_action_name = obj.animation_data.action.name if obj.animation_data and obj.animation_data.action else ""
        self.scene.lipsync_track_count = len([track for track in obj.animation_data.nla_tracks if self.LIPSYNC_PREFIX in track.name]) if obj.animation_data else 0
        
        self.scene.lipsync_shape_key_action_name = (obj.data.shape_keys.animation_data.action.name 
                                               if obj.data.shape_keys and obj.data.shape_keys.animation_data and obj.data.shape_keys.animation_data.action 
                                               else "")
        
        if self.scene.sequence_editor:
            audio_sequences = [seq.name for seq in self.scene.sequence_editor.sequences if seq.type == 'SOUND' and seq.name != "Background Music"]
            self.scene.lipsync_audio_sequences = ",".join(audio_sequences)
        else:
            self.scene.lipsync_audio_sequences = ""

    def check_new_lipsync_animation(self):
        obj = self.scene.lipsync_object
        if not obj:
            return False

        current_time = time.time()
        if current_time - self.scene.lipsync_last_modified < 1.0:
            return False

        current_action_name = ""
        if obj.animation_data and obj.animation_data.action:
            if self.LIPSYNC_PREFIX in obj.animation_data.action.name:
                current_action_name = obj.animation_data.action.name

        current_track_count = 0
        if obj.animation_data:
            current_track_count = len([track for track in obj.animation_data.nla_tracks if self.LIPSYNC_PREFIX in track.name])

        current_shape_key_action_name = ""
        if obj.data.shape_keys and obj.data.shape_keys.animation_data and obj.data.shape_keys.animation_data.action:
            if self.LIPSYNC_PREFIX in obj.data.shape_keys.animation_data.action.name:
                current_shape_key_action_name = obj.data.shape_keys.animation_data.action.name

        has_lipsync_animation = (current_action_name != "" or 
                                current_track_count > 0 or 
                                current_shape_key_action_name != "")

        if not has_lipsync_animation:
            return False

        has_changes = (current_action_name != self.scene.lipsync_action_name or
                    current_track_count != self.scene.lipsync_track_count or
                    current_shape_key_action_name != self.scene.lipsync_shape_key_action_name)

        if has_changes:
            if current_action_name != self.scene.lipsync_action_name:
                self.logger.info(f"检测到新动画: action变化 {self.scene.lipsync_action_name} -> {current_action_name}")
            if current_track_count != self.scene.lipsync_track_count:
                self.logger.info(f"检测到新动画: track数量变化 {self.scene.lipsync_track_count} -> {current_track_count}")
            if current_shape_key_action_name != self.scene.lipsync_shape_key_action_name:
                self.logger.info(f"检测到新动画: shape key action变化 {self.scene.lipsync_shape_key_action_name} -> {current_shape_key_action_name}")
            return True

        return False

    def get_next_available_start_frame(self):
        if not self.animation_queue:
            return self.scene.frame_current
        last_animation = self.animation_queue[-1]
        return max(self.scene.frame_current, last_animation['start_frame'] + last_animation['duration'])

    def handle_new_lipsync_animation(self):
        self.logger.info("开始处理新的唇形动画")
        self.mark_lipsync_animation()
        
        obj = self.scene.lipsync_object
        if not obj:
            self.logger.warning("没有找到唇形同步对象")
            return

        if not obj.animation_data:
            obj.animation_data_create()
        
        new_action = bpy.data.actions.get(self.scene.lipsync_action_name)
        audio_sequences = self.scene.lipsync_audio_sequences.split(",") if self.scene.lipsync_audio_sequences else []
        
        duration = 0
        if new_action:
            duration = max(duration, int(new_action.frame_range[1] - new_action.frame_range[0]))
        
        if self.scene.sequence_editor:
            for seq_name in audio_sequences:
                seq = self.scene.sequence_editor.sequences.get(seq_name)
                if seq and seq.type == 'SOUND':
                    duration = max(duration, seq.frame_duration)
        
        duration += self.EXTRA_FRAMES
        
        start_frame = max(
            self.scene.frame_current,
            self.current_animation_end_frame,
            self.get_next_available_start_frame()
        )
        
        self.logger.info(f"处理新的唇形同步动画, 选定起始帧:{start_frame}, 持续时间:{duration}")
        
        new_animation = {
            'action_name': self.scene.lipsync_action_name,
            'shape_key_action_name': self.scene.lipsync_shape_key_action_name,
            'audio_sequences': audio_sequences,
            'start_frame': start_frame,
            'duration': duration
        }
        
        self.animation_queue.append(new_animation)
        self.logger.info(f"新动画添加到队列,队列长度:{len(self.animation_queue)}")
        
        return new_animation

    def apply_next_animation(self):
        if not self.animation_queue:
            return None

        animation = self.animation_queue.popleft()
        obj = self.scene.lipsync_object
        if not obj:
            return None

        start_frame = animation['start_frame']
        self.logger.info(f"应用新动画,开始帧:{start_frame}")
        max_end_frame = start_frame + animation['duration']

        new_action = bpy.data.actions.get(animation['action_name'])
        if new_action:
            track = obj.animation_data.nla_tracks.new()
            track.name = f"{self.LIPSYNC_PREFIX}_{len(obj.animation_data.nla_tracks)}"
            
            strip = track.strips.new(name=new_action.name, start=start_frame, action=new_action)
            strip.frame_end = start_frame + animation['duration']
        
        if obj.data.shape_keys and obj.data.shape_keys.animation_data:
            shape_key_action = bpy.data.actions.get(animation['shape_key_action_name'])
            if shape_key_action:
                obj.data.shape_keys.animation_data.action = shape_key_action
                for fcurve in shape_key_action.fcurves:
                    for keyframe in fcurve.keyframe_points:
                        keyframe.co.x += start_frame
                        keyframe.handle_left.x += start_frame
                        keyframe.handle_right.x += start_frame

        if self.scene.sequence_editor:
            for seq_name in animation['audio_sequences']:
                seq = self.scene.sequence_editor.sequences.get(seq_name)
                if seq and seq.type == 'SOUND':
                    seq.frame_start = start_frame

        self.current_animation_end_frame = max_end_frame
        self.logger.info(f"新动画应用完成,结束帧:{self.current_animation_end_frame}")

        return max_end_frame

    def is_lipsync_animation_finished(self):
        obj = self.scene.lipsync_object
        if not obj or not obj.animation_data:
            return True

        current_frame = self.scene.frame_current
        for track in obj.animation_data.nla_tracks:
            if self.LIPSYNC_PREFIX in track.name:
                for strip in track.strips:
                    if strip.frame_start <= current_frame < strip.frame_end:
                        return False
        return current_frame >= self.current_animation_end_frame

    def clear_animations(self):
        self.animation_queue.clear()
        self.current_animation_end_frame = self.scene.frame_start