import bpy
import time
import os
import logging
from bpy.app.handlers import persistent
from frame_range_adjuster import FrameRangeAdjuster
import traceback
from typing import Optional, List
from lipsync_cleaner import LipSyncCleaner
from collections import deque
from .logger import get_logger
from .lipsync_animation_handler import LipSyncAnimationHandler

class VideoPlayer:
    COOLDOWN_TIME = 2.0
    EXTRA_FRAMES = 10
    MIN_ANIMATION_FRAMES = 10
    BG_MUSIC_NAME = "Background Music"
    MAX_FRAME = 100000

    def __init__(self, scene):
        self.logger = get_logger()
        self.scene = scene
        self.last_check_time = 0
        self.last_frame = self.scene.frame_current
        self.frame_range_adjuster = FrameRangeAdjuster(self.scene, self.EXTRA_FRAMES, self.MIN_ANIMATION_FRAMES)
        self.lipsync_cleaner = LipSyncCleaner(self.scene, LipSyncAnimationHandler.LIPSYNC_PREFIX, self.EXTRA_FRAMES, self.MIN_ANIMATION_FRAMES)
        self.lipsync_handler = LipSyncAnimationHandler(self.scene)
        bpy.app.handlers.frame_change_post.append(self.animation_handler)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.is_clearing = False
        self.original_end_frame = scene.frame_end
        self.playback_start_time = 0

    @property
    def lipsync_object(self) -> Optional[bpy.types.Object]:
        return self.scene.lipsync_object

    def handle_background_music(self, mute: bool = False):
        if self.scene.sequence_editor:
            bg_music = next((seq for seq in self.scene.sequence_editor.sequences if seq.name == self.BG_MUSIC_NAME), None)
            if bg_music:
                bg_music.mute = mute
                bg_music.frame_start = self.scene.frame_start
                bg_music.frame_final_end = self.scene.frame_end
                bg_music.volume = self.scene.bg_music_volume
                bg_music.sound.use_memory_cache = True
                bg_music.frame_offset_start = self.scene.frame_current - self.scene.frame_start
                if self.scene.is_playing:
                    bg_music.sound.use_mono = False

    def start_playback(self):
        self.scene.is_playing = True
        self.scene.frame_set(self.scene.frame_start)
        self.playback_start_time = time.time()
        self.handle_background_music()
        bpy.ops.screen.animation_play()

    def stop_playback(self):
        self.scene.is_playing = False
        bpy.ops.screen.animation_cancel(restore_frame=False)
        self.scene.frame_set(self.scene.frame_start)
        self.handle_background_music(mute=True)

    def pause_playback(self):
        self.scene.is_playing = False
        bpy.ops.screen.animation_cancel(restore_frame=True)
        self.handle_background_music(mute=True)

    def choose_bg_music(self, filepath: str):
        self.scene.custom_bg_music = filepath
        self.insert_background_music()

    def clear_lipsync_animation(self):
        self.is_clearing = True
        self.logger.info("开始清除唇形同步动画")
        self.lipsync_cleaner.clear_lipsync_animation()
        self.insert_background_music()
        self.lipsync_handler.clear_animations()
        self.is_clearing = False
        self.logger.info("唇形同步动画清除完成")

    def insert_background_music(self):
        if self.scene.custom_bg_music and os.path.exists(self.scene.custom_bg_music):
            bg_music_path = self.scene.custom_bg_music
        else:
            addon_dir = os.path.dirname(os.path.realpath(__file__))
            bg_music_path = os.path.join(addon_dir, "bg", "default.mp3")
        
        if os.path.exists(bg_music_path):
            if not self.scene.sequence_editor:
                self.scene.sequence_editor_create()
            
            existing_bg_music = next((seq for seq in self.scene.sequence_editor.sequences if seq.name == self.BG_MUSIC_NAME), None)
            if existing_bg_music:
                existing_bg_music.sound = bpy.data.sounds.load(bg_music_path)
                existing_bg_music.volume = self.scene.bg_music_volume
                existing_bg_music.frame_start = self.scene.frame_start
                existing_bg_music.frame_final_end = self.scene.frame_end
                existing_bg_music.mute = False
            else:
                try:
                    bg_sequence = self.scene.sequence_editor.sequences.new_sound(self.BG_MUSIC_NAME, bg_music_path, 1, self.scene.frame_start)
                    bg_sequence.frame_final_end = self.scene.frame_end
                    bg_sequence.volume = self.scene.bg_music_volume
                    bg_sequence.mute = False
                except Exception as e:
                    self.logger.error(f"Error inserting background music: {str(e)}")

    def clamp_frame_end(self, value):
        return max(1, min(value, self.MAX_FRAME))

    def reset_and_play(self):
        self.logger.info("开始 reset_and_play")
        self.clear_lipsync_animation()
        
        self.frame_range_adjuster.adjust_scene_frame_range()
        self.logger.info(f"调整后 - 开始帧: {self.scene.frame_start}, 结束帧: {self.scene.frame_end}")
        
        self.original_end_frame = self.scene.frame_end
        self.scene.frame_set(self.scene.frame_start)
        
        self.handle_background_music()
        self.scene.is_playing = False
        bpy.ops.screen.animation_play()
        if not self.scene.is_playing:
            self.scene.frame_current = self.scene.frame_start
            self.scene.is_playing = True
            bpy.context.scene.frame_set(self.scene.frame_current)       
        bpy.app.timers.register(self.check_animation_progress, first_interval=0.5)

    def check_animation_progress(self):
        if self.scene.frame_current == self.scene.frame_start:
            bpy.ops.screen.animation_play()
        return None

    def delayed_play(self):
        if not self.scene.is_playing:
            bpy.ops.screen.animation_play()
        else:
            self.logger.info("动画已经在播放中")
        return None

    def handle_end_of_animations(self):
        if self.scene.player_properties.panel_open:  # 只有在面板打开时才执行这个方法
            if self.scene.loop_playback:
                self.logger.info("检测到循环播放，执行重置操作")
                self.reset_and_play()
            else:
                self.logger.info("非循环播放，停止")
                self.stop_playback()

    def animation_handler(self, scene, depsgraph):
        if not self.scene.player_properties.panel_open:  # 如果面板没有打开，直接返回
            return

        current_time = time.time()
        current_frame = self.scene.frame_current

        if current_frame >= self.lipsync_handler.current_animation_end_frame and not self.is_clearing:
            if self.lipsync_handler.animation_queue:
                self.logger.info(f"当前帧 {current_frame} 已达到或超过当前动画结束帧 {self.lipsync_handler.current_animation_end_frame}")
                next_animation = self.lipsync_handler.animation_queue[0]
                self.logger.info(f"下一个动画起始帧: {next_animation['start_frame']}")
                if current_frame >= next_animation['start_frame']:
                    max_end_frame = self.lipsync_handler.apply_next_animation()
                    if max_end_frame:
                        self.scene.frame_end = self.clamp_frame_end(max(self.scene.frame_end, max_end_frame))
                        bg_music = next((seq for seq in self.scene.sequence_editor.sequences if seq.name == self.BG_MUSIC_NAME), None)
                        if bg_music:
                            bg_music.frame_final_end = self.scene.frame_end
                    self.logger.info(f"应用了下一个动画。当前动画结束帧: {self.lipsync_handler.current_animation_end_frame}, 场景结束帧: {self.scene.frame_end}")
                else:
                    self.logger.info("等待下一个动画的开始")
            elif current_frame >= self.scene.frame_end:
                if self.lipsync_handler.is_lipsync_animation_finished():
                    self.logger.info("所有动画已结束，处理结束逻辑")
                    self.handle_end_of_animations()
        elif self.original_end_frame < current_frame < self.scene.frame_end:
            self.logger.info(f"当前帧在原始结束帧和新结束帧之间，继续播放。当前帧：{current_frame}")
        else:
            self.last_frame = current_frame

        if (current_time - self.last_check_time) > self.COOLDOWN_TIME:
            self.last_check_time = current_time
            
            if self.lipsync_handler.check_new_lipsync_animation():
                self.logger.info("检测到新的唇形同步动画")
                new_animation = self.lipsync_handler.handle_new_lipsync_animation()
                if new_animation and len(self.lipsync_handler.animation_queue) == 1 and self.lipsync_handler.is_lipsync_animation_finished():
                    self.logger.info("队列之前为空且没有正在播放的唇形动画,立即应用新动画")
                    max_end_frame = self.lipsync_handler.apply_next_animation()
                    if max_end_frame:
                        self.scene.frame_end = self.clamp_frame_end(max(self.scene.frame_end, max_end_frame))
                        bg_music = next((seq for seq in self.scene.sequence_editor.sequences if seq.name == self.BG_MUSIC_NAME), None)
                        if bg_music:
                            bg_music.frame_final_end = self.scene.frame_end
                else:
                    self.logger.info("队列不为空或有正在播放的唇形动画,新动画将在当前动画结束后播放")

        self.handle_background_music()