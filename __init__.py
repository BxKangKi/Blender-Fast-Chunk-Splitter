bl_info = {
    "name": "Fast Chunk Splitter",
    "author": "AI Assistant",
    "version": (3, 1),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar(N) > Chunk Splitter",
    "description": "Splits meshes ultra-fast using Blender's native NumPy and BMesh.",
    "category": "Object",
}

# 애드온을 껐다 켤 때 main.py도 함께 새로고침 되도록 하는 블렌더 표준 코드
if "bpy" in locals():
    import importlib
    importlib.reload(main)
else:
    from . import main

import bpy

# --- 속성 (UI 설정값) ---
class ChunkSplitterProperties(bpy.types.PropertyGroup):
    chunks_x: bpy.props.IntProperty(
        name="X Chunks", default=4, min=1, max=100
    )
    chunks_y: bpy.props.IntProperty(
        name="Y Chunks", default=4, min=1, max=100
    )
    mode: bpy.props.EnumProperty(
        name="Mode",
        items=[
            ('BISECT', "Bisect Only (Hollow)", "Ultra-fast BMesh slicing. Leaves hollow insides."),
            ('SOLID', "Solid (Fill Sides)", "Uses Boolean modifier to create solid chunks.")
        ],
        default='BISECT'
    )

# --- 오퍼레이터 (실행 버튼 기능) ---
class CHUNK_OT_split_mesh(bpy.types.Operator):
    bl_idname = "chunk.split_mesh"
    bl_label = "Execute Fast Split"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target_obj = context.active_object
        if not target_obj or target_obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a Mesh object.")
            return {'CANCELLED'}

        settings = context.scene.chunk_splitter
        
        # main.py에 있는 핵심 알고리즘 함수 호출
        result = main.execute_split(
            context=context,
            target_obj=target_obj,
            chunks_x=settings.chunks_x,
            chunks_y=settings.chunks_y,
            mode=settings.mode,
            report_func=self.report # 에러나 완료 메시지를 띄우기 위해 리포트 함수 전달
        )

        return result

# --- UI 패널 (오른쪽 N 패널) ---
class CHUNK_PT_panel(bpy.types.Panel):
    bl_label = "Fast Chunk Splitter"
    bl_idname = "CHUNK_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Chunk Splitter"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.chunk_splitter

        box = layout.box()
        box.prop(settings, "chunks_x")
        box.prop(settings, "chunks_y")
        
        layout.separator()
        layout.prop(settings, "mode")
        layout.separator()
        
        layout.operator("chunk.split_mesh", icon='MESH_GRID')

classes = (ChunkSplitterProperties, CHUNK_OT_split_mesh, CHUNK_PT_panel)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.chunk_splitter = bpy.props.PointerProperty(type=ChunkSplitterProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.chunk_splitter

if __name__ == "__main__":
    register()