# __init__.py

bl_info = {
    "name": "Lip sync & 3D digital human",
    "author": "duke",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Lip Sync",
    "description": "Lip sync & 3D digital human",
    "category": "Animation",
}

import bpy
from . import lip_sync
from . import content_manager
from . import video_player
from .logger import get_logger

logger = get_logger()

class LIPSYNC_CONTENT_PT_main_panel(bpy.types.Panel):
    bl_label = "Lip Sync and Content Generation"
    bl_idname = "LIPSYNC_CONTENT_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Lip Sync'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "lipsync_content_tab", expand=True)

        if scene.lipsync_content_tab == 'CONTENT':
            content_manager.CONTENT_PT_panel.draw(self, context)
        elif scene.lipsync_content_tab == 'LIPSYNC':
            lip_sync.draw_panel(context, layout)
        elif scene.lipsync_content_tab == 'PLAYER':
            video_player.draw_player_controls(self, context, layout)

def register():
    logger.info("开始注册 Lip sync & 3D digital human 插件")
    
    bpy.utils.register_class(LIPSYNC_CONTENT_PT_main_panel)
    bpy.types.Scene.lipsync_content_tab = bpy.props.EnumProperty(
        items=[
            ('CONTENT', "内容生成", "Content generation tools"),
            ('LIPSYNC', "动画生成", "Lip sync animation tools"),
            ('PLAYER', "视频同步", "Video player")
        ],
        default='CONTENT'
    )

    content_manager.register()    
    lip_sync.register()
    video_player.register()
    
    logger.info("Lip sync & 3D digital human 插件注册完成")

def unregister():
    logger.info("开始注销 Lip sync & 3D digital human 插件")
    
    bpy.utils.unregister_class(LIPSYNC_CONTENT_PT_main_panel)
    del bpy.types.Scene.lipsync_content_tab

    content_manager.unregister()    
    lip_sync.unregister()
    video_player.unregister()
    
    logger.info("Lip sync & 3D digital human 插件注销完成")

if __name__ == "__main__":
    register()