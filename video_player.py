import bpy
from bpy.app.handlers import persistent
from .video_player_core import VideoPlayer

class PlayerProperties(bpy.types.PropertyGroup):
    panel_open: bpy.props.BoolProperty(default=False)

class PLAYER_OT_toggle_panel(bpy.types.Operator):
    bl_idname = "player.toggle_panel"
    bl_label = "Toggle Player Panel"
    bl_description = "打开或关闭播放器面板"

    def execute(self, context):
        context.scene.player_properties.panel_open = not context.scene.player_properties.panel_open
        return {'FINISHED'}

class PLAYER_OT_start_playback(bpy.types.Operator):
    bl_idname = "player.start_playback"
    bl_label = "开始播放"

    def execute(self, context):
        print("开始播放被调用")
        player = VideoPlayer(context.scene)
        try:
            player.start_playback()
            print("播放开始成功")
        except Exception as e:
            print(f"播放开始失败: {str(e)}")
            import traceback
            traceback.print_exc()
        return {'FINISHED'}

class PLAYER_OT_stop_playback(bpy.types.Operator):
    bl_idname = "player.stop_playback"
    bl_label = "停止播放"

    def execute(self, context):
        player = VideoPlayer(context.scene)
        player.stop_playback()
        return {'FINISHED'}

class PLAYER_OT_pause_playback(bpy.types.Operator):
    bl_idname = "player.pause_playback"
    bl_label = "暂停播放"

    def execute(self, context):
        player = VideoPlayer(context.scene)
        player.pause_playback()
        return {'FINISHED'}

class PLAYER_OT_choose_bg_music(bpy.types.Operator):
    bl_idname = "player.choose_bg_music"
    bl_label = "选择背景音乐"
    bl_description = "选择自定义背景音乐文件"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        player = VideoPlayer(context.scene)
        player.choose_bg_music(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def draw_player_controls(self, context, layout):
    scene = context.scene
    player_props = scene.player_properties
    
    # 添加切换面板的操作符
    layout.operator("player.toggle_panel", text="打开播放器面板", icon='TRIA_DOWN' if player_props.panel_open else 'TRIA_RIGHT')

    # 如果面板打开，才显示其他控件
    if player_props.panel_open:
        layout.operator("player.choose_bg_music", text="选择背景音乐")

        row = layout.row()
        if not scene.is_playing:
            row.operator("player.start_playback", text="开始播放")
        else:
            row.operator("player.pause_playback", text="暂停播放")
            row.operator("player.stop_playback", text="停止播放")

        layout.prop(scene, "loop_playback", text="循环播放")
        layout.prop(scene, "bg_music_volume", text="音乐音量")
        layout.prop(scene, "lipsync_object", text="LipSync对象")

@persistent
def animation_handler(scene):
    player = VideoPlayer(scene)
    player.animation_handler(scene, bpy.context.evaluated_depsgraph_get())

def register():
    bpy.utils.register_class(PlayerProperties)
    bpy.utils.register_class(PLAYER_OT_toggle_panel)
    bpy.utils.register_class(PLAYER_OT_start_playback)
    bpy.utils.register_class(PLAYER_OT_stop_playback)
    bpy.utils.register_class(PLAYER_OT_pause_playback)
    bpy.utils.register_class(PLAYER_OT_choose_bg_music)
    bpy.types.Scene.player_properties = bpy.props.PointerProperty(type=PlayerProperties)
    bpy.types.Scene.is_playing = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.loop_playback = bpy.props.BoolProperty(default=True, name="循环播放")
    bpy.types.Scene.bg_music_volume = bpy.props.FloatProperty(default=1.0, min=0.0, max=1.0, name="背景音乐音量")
    bpy.types.Scene.lipsync_last_modified = bpy.props.FloatProperty(default=0.0)
    bpy.types.Scene.lipsync_track_count = bpy.props.IntProperty(default=0)
    bpy.types.Scene.lipsync_action_name = bpy.props.StringProperty(default="")
    bpy.types.Scene.lipsync_shape_key_action_name = bpy.props.StringProperty(default="")
    bpy.types.Scene.lipsync_audio_sequences = bpy.props.StringProperty(default="")
    bpy.types.Scene.custom_bg_music = bpy.props.StringProperty(default="", subtype='FILE_PATH')
    bpy.types.Scene.lipsync_object = bpy.props.PointerProperty(type=bpy.types.Object, name="唇形对象")
    bpy.app.handlers.frame_change_post.append(animation_handler)

def unregister():
    bpy.utils.unregister_class(PlayerProperties)
    bpy.utils.unregister_class(PLAYER_OT_toggle_panel)
    bpy.utils.unregister_class(PLAYER_OT_start_playback)
    bpy.utils.unregister_class(PLAYER_OT_stop_playback)
    bpy.utils.unregister_class(PLAYER_OT_pause_playback)
    bpy.utils.unregister_class(PLAYER_OT_choose_bg_music)
    del bpy.types.Scene.player_properties
    del bpy.types.Scene.is_playing
    del bpy.types.Scene.loop_playback
    del bpy.types.Scene.bg_music_volume
    del bpy.types.Scene.lipsync_last_modified
    del bpy.types.Scene.lipsync_track_count
    del bpy.types.Scene.lipsync_action_name
    del bpy.types.Scene.lipsync_shape_key_action_name
    del bpy.types.Scene.lipsync_audio_sequences
    del bpy.types.Scene.custom_bg_music
    del bpy.types.Scene.lipsync_object
    bpy.app.handlers.frame_change_post.remove(animation_handler)

if __name__ == "__main__":
    register()