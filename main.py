import bpy
import bmesh
import numpy as np

def execute_split(context, target_obj, chunks_x, chunks_y, mode, report_func):
    """
    __init__.py에서 호출받아 실제 메쉬 분할을 수행하는 함수
    """
    target_name = target_obj.name

    # 1. 뷰포트 업데이트 정지 (속도 향상)
    bpy.context.view_layer.update()

    # 2. 메쉬 데이터 추출 및 월드 좌표 변환
    mesh = target_obj.data
    mesh.calc_loop_triangles()
    
    num_verts = len(mesh.vertices)
    num_tris = len(mesh.loop_triangles)

    if num_verts == 0 or num_tris == 0:
        report_func({'ERROR'}, "Selected mesh has no geometry.")
        return {'CANCELLED'}

    # --- [ NumPy 고속 필터링 (Early Rejection) ] ---
    report_func({'INFO'}, "Analyzing geometry with NumPy...")
    
    # 정점(Vertex) 좌표 추출
    verts = np.empty(num_verts * 3, dtype=np.float32)
    mesh.vertices.foreach_get('co', verts)
    verts.shape = (num_verts, 3)

    # 월드 매트릭스 적용
    mat = np.array(target_obj.matrix_world)
    verts_pad = np.c_[verts, np.ones(num_verts)]
    verts_world = np.dot(verts_pad, mat.T)[:, :3]

    # 삼각형(Triangle) 인덱스 추출
    tri_indices = np.empty(num_tris * 3, dtype=np.int32)
    mesh.loop_triangles.foreach_get('vertices', tri_indices)
    tri_indices.shape = (num_tris, 3)

    # 각 삼각형의 좌표 할당
    tri_verts = verts_world[tri_indices]

    # 모든 삼각형의 X, Y 최소/최대값 계산 (순식간에 처리됨)
    tri_min_x = tri_verts[:, :, 0].min(axis=1)
    tri_max_x = tri_verts[:, :, 0].max(axis=1)
    tri_min_y = tri_verts[:, :, 1].min(axis=1)
    tri_max_y = tri_verts[:, :, 1].max(axis=1)

    # 전체 Bounding Box 계산
    min_x, max_x = tri_min_x.min(), tri_max_x.max()
    min_y, max_y = tri_min_y.min(), tri_max_y.max()
    min_z, max_z = verts_world[:, 2].min(), verts_world[:, 2].max()

    chunk_w_x = (max_x - min_x) / chunks_x
    chunk_w_y = (max_y - min_y) / chunks_y
    height = max_z - min_z + 10.0 # Z축은 넉넉하게

    # 결과물을 담을 컬렉션 생성
    chunk_collection = bpy.data.collections.new(f"{target_name}_Chunks")
    context.scene.collection.children.link(chunk_collection)

    created_count = 0
    cutter = None
    bm_orig = None
    
    # --- [ BISECT 모드 셋업 ] ---
    if mode == 'BISECT':
        bm_orig = bmesh.new()
        bm_orig.from_mesh(mesh)
        bm_orig.transform(target_obj.matrix_world)

    # --- [ SOLID 모드 셋업 (Cutter 생성) ] ---
    elif mode == 'SOLID':
        bpy.ops.mesh.primitive_cube_add(size=1)
        cutter = context.active_object
        cutter.name = "Temp_Cutter"
        cutter.scale = (chunk_w_x, chunk_w_y, height)
        cutter.display_type = 'BOUNDS'
        cutter.hide_render = True

    # --- [ 청크 분할 루프 ] ---
    for i in range(chunks_x):
        for j in range(chunks_y):
            c_min_x = min_x + i * chunk_w_x
            c_max_x = min_x + (i + 1) * chunk_w_x
            c_min_y = min_y + j * chunk_w_y
            c_max_y = min_y + (j + 1) * chunk_w_y

            # NumPy를 이용한 교차 검사 (빈 허공이면 스킵)
            mask = (tri_min_x <= c_max_x) & (tri_max_x >= c_min_x) & \
                   (tri_min_y <= c_max_y) & (tri_max_y >= c_min_y)
            
            if not np.any(mask):
                continue # 지오메트리가 없는 구역 스킵

            chunk_name = f"{target_name}_{i}_{j}"

            # 1. BISECT 방식 (인메모리 BMesh 슬라이싱)
            if mode == 'BISECT':
                bm = bm_orig.copy()
                
                planes = [
                    ((c_min_x, 0, 0), (1, 0, 0)),
                    ((c_max_x, 0, 0), (-1, 0, 0)),
                    ((0, c_min_y, 0), (0, 1, 0)),
                    ((0, c_max_y, 0), (0, -1, 0))
                ]
                
                for p_co, p_no in planes:
                    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
                    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=p_co, plane_no=p_no, clear_inner=True, clear_outer=False)

                if len(bm.faces) > 0:
                    new_mesh = bpy.data.meshes.new(chunk_name)
                    bm.transform(target_obj.matrix_world.inverted()) # 로컬 좌표로 복귀
                    bm.to_mesh(new_mesh)
                    new_obj = bpy.data.objects.new(chunk_name, new_mesh)
                    new_obj.matrix_world = target_obj.matrix_world
                    chunk_collection.objects.link(new_obj)
                    created_count += 1
                    
                bm.free()

            # 2. SOLID 방식 (Boolean Modifier)
            elif mode == 'SOLID':
                pos_x = c_min_x + (chunk_w_x / 2)
                pos_y = c_min_y + (chunk_w_y / 2)
                pos_z = min_z + (height / 2) - 5.0
                
                cutter.location = (pos_x, pos_y, pos_z)
                context.view_layer.update()

                new_obj = target_obj.copy()
                new_obj.data = target_obj.data.copy()
                new_obj.name = chunk_name
                chunk_collection.objects.link(new_obj)

                bool_mod = new_obj.modifiers.new(name="Chunk_Split", type='BOOLEAN')
                bool_mod.operation = 'INTERSECT'
                bool_mod.object = cutter
                bool_mod.solver = 'FAST'

                context.view_layer.objects.active = new_obj
                bpy.ops.object.modifier_apply(modifier="Chunk_Split")

                if len(new_obj.data.vertices) == 0:
                    mesh_to_remove = new_obj.data
                    bpy.data.objects.remove(new_obj, do_unlink=True)
                    bpy.data.meshes.remove(mesh_to_remove, do_unlink=True)
                else:
                    created_count += 1

    # --- [ 뒷정리 ] ---
    if mode == 'BISECT' and bm_orig:
        bm_orig.free()
    elif mode == 'SOLID' and cutter:
        bpy.data.objects.remove(cutter, do_unlink=True)

    if created_count > 0:
        target_obj.hide_viewport = True
        target_obj.hide_render = True
        report_func({'INFO'}, f"Success! Generated {created_count} chunks.")
    else:
        report_func({'WARNING'}, "No chunks generated.")

    return {'FINISHED'}