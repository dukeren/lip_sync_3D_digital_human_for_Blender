import bpy
import random

class IdleAnimationGenerator:
    def __init__(self):
        pass

    def clear_all_idle_animations(self, obj):
        # 清除所有与闲置动画相关的数据
        if obj.animation_data:
            # 清除所有以"Idle_"开头的NLA轨道
            if obj.animation_data.nla_tracks:
                tracks_to_remove = [track for track in obj.animation_data.nla_tracks if track.name.startswith("Idle_") or track.name == "Idle"]
                for track in tracks_to_remove:
                    obj.animation_data.nla_tracks.remove(track)

        # 清除形态键的动画数据
        if obj.data.shape_keys and obj.data.shape_keys.animation_data:
            if obj.data.shape_keys.animation_data.action:
                action = obj.data.shape_keys.animation_data.action
                # 清除所有与形态键相关的 FCurves
                fcurves_to_remove = [fc for fc in action.fcurves if fc.data_path.startswith("key_blocks")]
                for fc in fcurves_to_remove:
                    action.fcurves.remove(fc)

            # 清除所有以"Idle_"开头的NLA轨道
            if obj.data.shape_keys.animation_data.nla_tracks:
                tracks_to_remove = [track for track in obj.data.shape_keys.animation_data.nla_tracks if track.name.startswith("Idle_") or track.name == "Idle"]
                for track in tracks_to_remove:
                    obj.data.shape_keys.animation_data.nla_tracks.remove(track)

        # 重置所有形态键的值
        if obj.data.shape_keys:
            for key_block in obj.data.shape_keys.key_blocks:
                if key_block.name != 'Basis':  # 不重置基础形态
                    key_block.value = 0

        # 删除所有未使用的闲置动作
        for action in bpy.data.actions:
            if action.name.startswith("IdleAction_") or action.name == "IdleAction":
                if action.users == 0:
                    bpy.data.actions.remove(action)

    def generate_idle_animations(self, context):
        # 使用自定义帧数或场景的结束帧
        total_frames = context.scene.lip_sync.custom_frames if context.scene.lip_sync.custom_frames > 0 else context.scene.frame_end

        for index, idle_anim in enumerate(context.scene.lip_sync.idle_animations):
            if not idle_anim.object:
                print(f"警告: 闲置动画 '{idle_anim.name}' 没有选择对象，跳过")
                continue

            obj = idle_anim.object
            if obj.type != 'MESH':
                print(f"警告: 对象 '{obj.name}' 不是网格对象，跳过")
                continue

            if not obj.data.shape_keys:
                print(f"警告: 对象 '{obj.name}' 没有形态键，跳过")
                continue

            if idle_anim.shape_key not in obj.data.shape_keys.key_blocks:
                print(f"警告: 对象 '{obj.name}' 中找不到形态键 '{idle_anim.shape_key}'，跳过")
                continue

            # 创建新的动作来存储闲置动画
            idle_action = bpy.data.actions.new(name=f"IdleAction_{idle_anim.shape_key}_{index}")
            
            # 确保对象有动画数据
            if not obj.data.shape_keys.animation_data:
                obj.data.shape_keys.animation_data_create()
            
            # 临时设置当前动作为闲置动画
            original_action = obj.data.shape_keys.animation_data.action
            obj.data.shape_keys.animation_data.action = idle_action

            shape_key = obj.data.shape_keys.key_blocks[idle_anim.shape_key]
            frame = 0
            while frame < total_frames:
                interval = random.uniform(idle_anim.min_interval, idle_anim.max_interval)
                duration = random.uniform(idle_anim.min_duration, idle_anim.max_duration)
                
                start_frame = int(frame)
                mid_frame = int(frame + duration * 0.5)
                end_frame = int(frame + duration)
                
                # 创建关键帧
                shape_key.value = 0
                shape_key.keyframe_insert("value", frame=start_frame)
                
                shape_key.value = 1
                shape_key.keyframe_insert("value", frame=mid_frame)
                
                shape_key.value = 0
                shape_key.keyframe_insert("value", frame=end_frame)
                
                frame += duration + interval

            # 创建NLA轨道和条带
            nla_tracks = obj.data.shape_keys.animation_data.nla_tracks
            idle_track = nla_tracks.new()
            idle_track.name = f"Idle_{idle_anim.shape_key}_{index}"
            
            idle_strip = idle_track.strips.new(f"Strips_{idle_anim.shape_key}_{index}", start=1, action=idle_action)
            idle_strip.blend_type = 'ADD'
            idle_strip.use_auto_blend = False
            idle_strip.influence = 1.0

        context.scene.frame_start = 1
        context.scene.frame_end = total_frames

        print(f"清除了现有闲置动画并生成了新的闲置动画，场景帧范围设置为 1 - {total_frames}")
        return {'FINISHED'}