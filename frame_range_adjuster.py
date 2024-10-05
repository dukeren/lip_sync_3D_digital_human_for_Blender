import bpy
import time
import logging
from bpy.app.handlers import persistent

class FrameRangeAdjuster:
    def __init__(self, scene, extra_frames, min_animation_frames):
        self.scene = scene
        self.EXTRA_FRAMES = extra_frames
        self.MIN_ANIMATION_FRAMES = min_animation_frames
        self.max_end_frame = self.scene.frame_start
        self.last_processed_time = 0
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def adjust_scene_frame_range(self):
        try:
            current_time = time.time()
            if current_time - self.last_processed_time < 5:  # 5秒冷却时间
                return self.scene.frame_end
            self.last_processed_time = current_time

            return self._adjust_scene_frame_range_main()
        except Exception as e:
            self.logger.error(f"Error in adjust_scene_frame_range: {str(e)}")
            return self.scene.frame_end

    def _adjust_scene_frame_range_main(self):
        try:
            self.max_end_frame = self.scene.frame_start
            self.logger.info(f"Initial max_end_frame: {self.max_end_frame}")

            for obj in self.scene.objects:
                self._process_object(obj)

            proposed_end_frame = int(self.max_end_frame + self.EXTRA_FRAMES)
            proposed_end_frame = max(proposed_end_frame, self.scene.frame_start + self.MIN_ANIMATION_FRAMES)
            self.logger.info(f"Proposed: {proposed_end_frame}, Minimum: {self.MIN_ANIMATION_FRAMES}")

            if proposed_end_frame != self.scene.frame_end:
                self.logger.info(f"Updating scene frame range. Original: {self.scene.frame_end}, New: {proposed_end_frame}")
                self.scene.frame_end = proposed_end_frame

            return self.scene.frame_end
        except Exception as e:
            self.logger.error(f"Error in _adjust_scene_frame_range_main: {str(e)}")
            return self.scene.frame_end

    def _process_object(self, obj):
        try:
            if obj is None or obj.name not in bpy.data.objects:
                self.logger.warning(f"Skipping invalid object: {obj}")
                return

            self._process_animation_data(obj.animation_data)
            if obj.type == 'MESH' and obj.data and obj.data.shape_keys:
                self._process_animation_data(obj.data.shape_keys.animation_data)
        except Exception as e:
            self.logger.error(f"Error processing object {obj.name if obj else 'None'}: {str(e)}")

    def _process_animation_data(self, anim_data):
        if not anim_data:
            return

        try:
            if anim_data.action:
                self.max_end_frame = max(self.max_end_frame, anim_data.action.frame_range[1])

            for track in anim_data.nla_tracks:
                for strip in track.strips:
                    self.max_end_frame = max(self.max_end_frame, strip.frame_end)

            for fc in anim_data.drivers:
                if fc.keyframe_points:
                    self.max_end_frame = max(self.max_end_frame, max(kf.co.x for kf in fc.keyframe_points))
        except Exception as e:
            self.logger.error(f"Error processing animation data: {str(e)}")

@persistent
def scene_update_handler(dummy):
    try:
        scene = bpy.context.scene
        adjuster = FrameRangeAdjuster(scene, 10, 10)
        adjuster.adjust_scene_frame_range()
    except Exception as e:
        logging.error(f"Error in scene_update_handler: {str(e)}")

def register():
    bpy.app.handlers.depsgraph_update_post.append(scene_update_handler)
    logging.info("FrameRangeAdjuster registered")

def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(scene_update_handler)
    logging.info("FrameRangeAdjuster unregistered")

if __name__ == "__main__":
    register()