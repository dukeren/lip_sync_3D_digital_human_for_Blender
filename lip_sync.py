import sys
import bpy
import os
import logging
import time
from bpy.props import StringProperty, BoolProperty, FloatProperty, IntProperty, EnumProperty, CollectionProperty, PointerProperty
from bpy_extras.io_utils import ImportHelper

sys.path.append(os.path.dirname(__file__))
from lip_sync_core import LipSyncCore
from lip_sync_idle_animation_generator import IdleAnimationGenerator

# Configure logging
logger = logging.getLogger("LipSyncLogger")
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

class IdleAnimation(bpy.types.PropertyGroup):
    name: StringProperty(name="名称")
    object: PointerProperty(name="对象", type=bpy.types.Object)
    shape_key: StringProperty(name="形态键")
    min_interval: FloatProperty(name="最小间隔", default=1.0, min=0.1)
    max_interval: FloatProperty(name="最大间隔", default=5.0, min=0.1)
    min_duration: FloatProperty(name="最小持续时间", default=0.1, min=0.1)
    max_duration: FloatProperty(name="最大持续时间", default=1.0, min=0.1)

class LipSyncProperties(bpy.types.PropertyGroup):
    audio_file: StringProperty(name="音频文件", default="")
    is_listening: BoolProperty(name="监听音频", default=False)
    frame_rate: FloatProperty(name="帧率", default=24.0)
    silence_threshold: FloatProperty(name="静音阈值", default=0.01, min=0.0, max=1.0)
    max_silence_frames: IntProperty(name="最大静音帧数", default=5, min=1)
    monitor_folder: StringProperty(name="监听文件夹", default=os.path.join(os.path.dirname(__file__), 'Voice'), subtype='DIR_PATH')
    is_monitoring: BoolProperty(name="正在监听", default=False)
    idle_animations: CollectionProperty(type=IdleAnimation)
    active_idle_animation: IntProperty(default=0)
    custom_frames: IntProperty(name="自定义帧数", description="设置自定义的总帧数，留空或设为0则使用场景的结束帧", min=0, default=0)
    mouth_object: PointerProperty(name="唇型对象", type=bpy.types.Object)
    language: EnumProperty(
        name="语言",
        items=[
            ('chinese', "中文", "使用中文音素到口型映射"),
            ('english', "英文", "使用英文音素到口型映射")
        ],
        default='chinese'
    )

class LIPSYNC_OT_select_audio(bpy.types.Operator, ImportHelper):
    bl_idname = "lipsync.select_audio"
    bl_label = "选择音频文件"
    
    filter_glob: StringProperty(default="*.wav;*.mp3", options={'HIDDEN'})

    def execute(self, context):
        context.scene.lip_sync.audio_file = self.filepath
        logger.info(f"选择的音频文件: {self.filepath}")
        return {'FINISHED'}

class LIPSYNC_OT_select_monitor_folder(bpy.types.Operator, ImportHelper):
    bl_idname = "lipsync.select_monitor_folder"
    bl_label = "选择监听文件夹"
    
    directory: StringProperty(subtype='DIR_PATH')

    def execute(self, context):
        context.scene.lip_sync.monitor_folder = self.directory
        logger.info(f"选择的监听文件夹: {self.directory}")
        return {'FINISHED'}

class LIPSYNC_OT_analyze_audio(bpy.types.Operator):
    bl_idname = "lipsync.analyze_audio"
    bl_label = "分析音频"

    def execute(self, context):
        audio_file = context.scene.lip_sync.audio_file
        if not audio_file:
            self.report({'ERROR'}, "未选择音频文件")
            logger.error("错误: 未选择音频文件")
            return {'CANCELLED'}
        
        self.analyze_and_apply(context, audio_file)
        return {'FINISHED'}

    def analyze_and_apply(self, context, audio_file):
        lip_sync_core = LipSyncCore(
            frame_rate=context.scene.lip_sync.frame_rate,
            silence_threshold=context.scene.lip_sync.silence_threshold,
            max_silence_frames=context.scene.lip_sync.max_silence_frames,
            language=context.scene.lip_sync.language
        )
        
        mouth_object = context.scene.lip_sync.mouth_object
        
        if mouth_object is None or mouth_object.type != 'MESH':
            self.report({'ERROR'}, f"未选择有效的唇形网格对象")
            logger.error(f"错误: 未选择有效的唇型网格对象")
            return
        
        if mouth_object.data.shape_keys is None:
            self.report({'ERROR'}, f"口型对象 '{mouth_object.name}' 没有形态键")
            logger.error(f"错误: 口型对象 '{mouth_object.name}' 没有形态键")
            return
        
        logger.info(f"口型对象: {mouth_object.name}, 类型: {mouth_object.type}")
        
        try:
            # 分析音频并生成口型数据
            visemes = lip_sync_core.analyze_audio(audio_file)
            logger.info(f"生成的visemes数量: {len(visemes)}")
            
            # 应用口型数据到网格对象
            action_name = f"LipSync_{int(time.time())}"
            lip_sync_action = lip_sync_core.apply_visemes_to_mesh(mouth_object, visemes, action_name)
            logger.info(f"创建的动作: {lip_sync_action.name}")
            
            # 创建NLA轨道和条带
            track_name = f"LipSync_Track_{int(time.time())}"
            strip_name = f"LipSync_Strip_{int(time.time())}"
            lip_sync_core.create_nla_track(mouth_object, lip_sync_action, track_name, strip_name)
            logger.info(f"创建了NLA轨道: {track_name}, 条带: {strip_name}")
            
            # 清除之前的音频(如果有)
            if context.scene.sequence_editor:
                for seq in context.scene.sequence_editor.sequences_all:
                    if seq.type == 'SOUND':
                        context.scene.sequence_editor.sequences.remove(seq)
                logger.info("清除了之前的音频")

            # 插入新的音频
            if not context.scene.sequence_editor:
                context.scene.sequence_editor_create()

            sound_strip = context.scene.sequence_editor.sequences.new_sound(
                name="LipSync Audio",
                filepath=audio_file,
                channel=1,
                frame_start=1
            )
            logger.info(f"插入了新的音频: {audio_file}")
            logger.info(f"音频条带名称: {sound_strip.name}, 持续时间: {sound_strip.frame_duration} 帧")

            # 可选：设置音量或其他属性
            sound_strip.volume = 1.0  # 设置音量为100%

            self.report({'INFO'}, f"完成了唇形同步,并插入了音频")
            logger.info(f"完成了唇形同步,并插入了音频")

        except Exception as e:
            self.report({'ERROR'}, f"处理过程中发生错误: {str(e)}")
            logger.error(f"处理过程中发生错误: {str(e)}")
            logger.error(f"错误类型: {type(e).__name__}")
            logger.error(f"错误发生位置: {e.__traceback__.tb_frame.f_code.co_filename}, 行号: {e.__traceback__.tb_lineno}")
            return {'CANCELLED'}

class LIPSYNC_OT_monitor_folder(bpy.types.Operator):
    bl_idname = "lipsync.monitor_folder"
    bl_label = "监听文件夹"
    
    _timer = None
    _last_files = set()

    def modal(self, context, event):
        if event.type == 'TIMER':
            if not context.scene.lip_sync.is_listening:
                self.cancel(context)
                return {'CANCELLED'}
            
            monitor_folder = context.scene.lip_sync.monitor_folder
            current_files = set(os.listdir(monitor_folder))
            new_files = current_files - self._last_files
            
            if new_files:
                for file in new_files:
                    file_path = os.path.join(monitor_folder, file)
                    if file.lower().endswith(('.wav', '.mp3')):
                        logger.info(f"检测到新的音频文件: {file}")
                        context.scene.lip_sync.audio_file = file_path
                        bpy.ops.lipsync.analyze_audio()
                
                self._last_files = current_files
        
        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(1.0, window=context.window)
        wm.modal_handler_add(self)
        self._last_files = set(os.listdir(context.scene.lip_sync.monitor_folder))
        logger.info(f"开始监听文件夹: {context.scene.lip_sync.monitor_folder}")
        logger.info(f"初始文件列表: {self._last_files}")
        logger.info(f"监听状态: {context.scene.lip_sync.is_listening}")
        context.scene.lip_sync.is_monitoring = True
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        if self._timer is not None:
            wm.event_timer_remove(self._timer)
            self._timer = None
        logger.info("停止监听文件夹")
        context.scene.lip_sync.is_monitoring = False

    def invoke(self, context, event):
        if context.scene.lip_sync.is_monitoring:
            self.cancel(context)
            return {'CANCELLED'}
        else:
            return self.execute(context)

class LIPSYNC_OT_add_idle_animation(bpy.types.Operator):
    bl_idname = "lipsync.add_idle_animation"
    bl_label = "添加闲置动画"

    def execute(self, context):
        idle_anims = context.scene.lip_sync.idle_animations
        new_anim = idle_anims.add()
        new_anim.name = f"IdleAnimation{len(idle_anims)}"
        return {'FINISHED'}

class LIPSYNC_OT_remove_idle_animation(bpy.types.Operator):
    bl_idname = "lipsync.remove_idle_animation"
    bl_label = "移除闲置动画"

    index: IntProperty()

    def execute(self, context):
        idle_anims = context.scene.lip_sync.idle_animations
        idle_anims.remove(self.index)
        return {'FINISHED'}

class LIPSYNC_OT_generate_idle_animations(bpy.types.Operator):
    bl_idname = "lipsync.generate_idle_animations"
    bl_label = "生成闲置动画"

    def execute(self, context):
        generator = IdleAnimationGenerator()
        return generator.generate_idle_animations(context)

class LIPSYNC_OT_clear_idle_animations(bpy.types.Operator):
    bl_idname = "lipsync.clear_idle_animations"
    bl_label = "清除闲置动画"
    bl_description = "清除所有对象的闲置动画"

    def execute(self, context):
        generator = IdleAnimationGenerator()
        for idle_anim in context.scene.lip_sync.idle_animations:
            if idle_anim.object:
                generator.clear_all_idle_animations(idle_anim.object)
        self.report({'INFO'}, "已清除所有闲置动画")
        return {'FINISHED'}

def draw_panel(context, layout):
    lip_sync = context.scene.lip_sync

    row = layout.row()
    row.prop(lip_sync, "is_listening", text="检测音频")
    if lip_sync.is_listening:
        row.operator("lipsync.select_monitor_folder", text="选择检测文件夹")
        layout.prop(lip_sync, "monitor_folder", text="")
        if not lip_sync.monitor_folder:
            layout.label(text="请选择监听文件夹", icon='ERROR')
        else:
            if lip_sync.is_monitoring:
                layout.operator("lipsync.monitor_folder", text="停止检测")
            else:
                layout.operator("lipsync.monitor_folder", text="开始检测")
    else:
        row.operator("lipsync.select_audio", text="选择音频文件")
        layout.prop(lip_sync, "audio_file", text="")
        layout.operator("lipsync.analyze_audio", text="分析并应用")

    layout.separator()
    layout.prop(lip_sync, "mouth_object", text="唇型对象")
    layout.prop(lip_sync, "frame_rate", text="帧率")
    layout.prop(lip_sync, "silence_threshold", text="静音阈值")
    layout.prop(lip_sync, "max_silence_frames", text="最大静音帧数")
    layout.prop(lip_sync, "language", text="语言")

    layout.separator()
    layout.label(text="闲置动画:")
    layout.prop(lip_sync, "custom_frames", text="自定义帧数")
    for i, anim in enumerate(lip_sync.idle_animations):
        box = layout.box()
        row = box.row()
        row.prop(anim, "name", text="")
        row.operator("lipsync.remove_idle_animation", text="", icon='X').index = i
        box.prop(anim, "object", text="对象")
        box.prop(anim, "shape_key", text="形态键")
        box.prop(anim, "min_interval", text="最小间隔")
        box.prop(anim, "max_interval", text="最大间隔")
        box.prop(anim, "min_duration", text="最小持续时间")
        box.prop(anim, "max_duration", text="最大持续时间")

    layout.operator("lipsync.add_idle_animation", text="添加闲置动画")
    layout.operator("lipsync.generate_idle_animations", text="生成闲置动画")
    layout.operator("lipsync.clear_idle_animations", text="清除闲置动画")

classes = (
    IdleAnimation,
    LipSyncProperties,
    LIPSYNC_OT_select_audio,
    LIPSYNC_OT_analyze_audio,
    LIPSYNC_OT_select_monitor_folder,
    LIPSYNC_OT_monitor_folder,
    LIPSYNC_OT_add_idle_animation,
    LIPSYNC_OT_remove_idle_animation,
    LIPSYNC_OT_generate_idle_animations,
    LIPSYNC_OT_clear_idle_animations,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.lip_sync = bpy.props.PointerProperty(type=LipSyncProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.lip_sync

if __name__ == "__main__":
    register()