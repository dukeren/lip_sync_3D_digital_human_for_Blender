import bpy
import threading
from frame_range_adjuster import FrameRangeAdjuster

class LipSyncCleaner:
    def __init__(self, scene, lipsync_prefix, extra_frames, min_animation_frames):
        self.scene = scene
        self.LIPSYNC_PREFIX = lipsync_prefix
        self.frame_range_adjuster = FrameRangeAdjuster(self.scene, extra_frames, min_animation_frames)

    def clear_lipsync_animation(self):
        obj = self.scene.lipsync_object
        if not obj:
            return

        if obj.animation_data:
            for track in [track for track in obj.animation_data.nla_tracks if self.LIPSYNC_PREFIX in track.name]:
                obj.animation_data.nla_tracks.remove(track)
            if obj.animation_data.action and self.LIPSYNC_PREFIX in obj.animation_data.action.name:
                obj.animation_data.action = None

        if obj.data.shape_keys and obj.data.shape_keys.animation_data:
            if obj.data.shape_keys.animation_data.action and self.LIPSYNC_PREFIX in obj.data.shape_keys.animation_data.action.name:
                obj.data.shape_keys.animation_data.action = None

        if self.scene.sequence_editor:
            for seq in [seq for seq in self.scene.sequence_editor.sequences if seq.type == 'SOUND' and seq.name != "Background Music"]:
                self.scene.sequence_editor.sequences.remove(seq)

        for action in bpy.data.actions:
            if self.LIPSYNC_PREFIX in action.name and action.users == 0:
                bpy.data.actions.remove(action)
        
        for sound in bpy.data.sounds:
            if sound.users == 0:
                bpy.data.sounds.remove(sound)

        threading.Thread(target=self.threaded_adjust_scene_frame_range).start()

    def threaded_adjust_scene_frame_range(self):
        new_end_frame = self.frame_range_adjuster.adjust_scene_frame_range()