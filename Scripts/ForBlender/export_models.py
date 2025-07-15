import bpy
import os
import shutil
import glob
import addon_utils

# ----------- 配置区 ----------- 
# 只需设置这两个变量
base_export_dir = r"C:\Users\Administrator\Desktop\Assets\TestModels\Models"
model_name = "BurjKhalifaDubai"  # 文件名和文件夹名

# ----------- 工具函数 -----------

def ensure_addon_enabled(module_name):
    if not addon_utils.check(module_name)[1]:
        addon_utils.enable(module_name, default_set=True, persistent=True)

def get_all_image_paths():
    image_paths = set()
    for img in bpy.data.images:
        if img.filepath and img.source == 'FILE':
            abs_path = bpy.path.abspath(img.filepath)
            if os.path.isfile(abs_path):
                image_paths.add(abs_path)
            else:
                print(f"Invalid texture path: {abs_path}")
    return list(image_paths)

def copy_textures_to_dir(target_dir):
    image_paths = get_all_image_paths()
    for img_path in image_paths:
        try:
            print(f"Copying {img_path} to {target_dir}")
            shutil.copy(img_path, target_dir)
        except Exception as e:
            print(f"Failed to copy {img_path}: {e}")

def move_textures_to_fbm(fbx_dir, fbx_name):
    textures_dir = os.path.join(fbx_dir, "Textures")
    fbm_dir = os.path.join(fbx_dir, f"{fbx_name}.fbm")
    os.makedirs(fbm_dir, exist_ok=True)
    print(f"Moving textures from {textures_dir} to {fbm_dir}")
    if os.path.exists(textures_dir):
        for file in os.listdir(textures_dir):
            src = os.path.join(textures_dir, file)
            dst = os.path.join(fbm_dir, file)
            shutil.move(src, dst)
        os.rmdir(textures_dir)

# ----------- 主流程 -----------

# 启用导出插件
ensure_addon_enabled("io_scene_obj")
ensure_addon_enabled("io_scene_gltf2")
ensure_addon_enabled("io_scene_fbx")

# 统计面数
total_faces = sum([obj.data.polygons.__len__() for obj in bpy.data.objects if obj.type == 'MESH'])
faces_k = int(round(total_faces / 1000))

# 生成根目录
export_root = os.path.join(base_export_dir, f"{model_name}_{faces_k}k")

# 生成子目录
export_paths = {
    "fbx": os.path.join(export_root, "Fbx"),
    "gltf": os.path.join(export_root, "glTF"),
    "glb": os.path.join(export_root, "glb"),
    "obj": os.path.join(export_root, "obj"),
}

# 创建目录
for key, path in export_paths.items():
    os.makedirs(path, exist_ok=True)
    if key in ["fbx", "gltf", "obj"]:
        tex_dir = os.path.join(path, "Textures")
        os.makedirs(tex_dir, exist_ok=True)
        print(f"Created texture directory: {tex_dir}")

# 统一文件名
file_name = model_name

# --- FBX ---
fbx_path = os.path.join(export_paths["fbx"], f"{file_name}.fbx")
bpy.ops.export_scene.fbx(
    filepath=fbx_path,
    use_selection=False,
    path_mode='COPY',  # 使用复制模式
    embed_textures=False,
    batch_mode='OFF'
)

# --- glTF (.gltf + .bin + 纹理) ---
gltf_path = os.path.join(export_paths["gltf"], f"{file_name}.gltf")
bpy.ops.export_scene.gltf(
    filepath=gltf_path,
    export_format='GLTF_SEPARATE',
    export_texture_dir="Textures",
    use_selection=False
)

# --- GLB (单文件) ---
glb_path = os.path.join(export_paths["glb"], f"{file_name}.glb")
bpy.ops.export_scene.gltf(
    filepath=glb_path,
    export_format='GLB',
    use_selection=False
)

# --- OBJ ---
# OBJ导出时，确保使用正确的路径和材质
obj_path = os.path.join(export_paths["obj"], f"{file_name}.obj")

# 确保纹理文件已经准备好，如果需要的话可以手动复制
copy_textures_to_dir(os.path.join(export_paths["obj"], "Textures"))

bpy.ops.wm.obj_export(
    filepath=obj_path,
    export_selected_objects=False,
    export_materials=True,  # 确保材质被导出
    export_triangulated_mesh=False,
    export_normals=True,
    export_uv=True,
)

# 移动贴图到 obj/Textures
def move_obj_textures(obj_dir):
    tex_dir = os.path.join(obj_dir, "Textures")
    os.makedirs(tex_dir, exist_ok=True)
    print(f"Moving OBJ textures to {tex_dir}")
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.tga", "*.bmp", "*.tiff", "*.exr"):
        for img_file in glob.glob(os.path.join(obj_dir, ext)):
            try:
                shutil.move(img_file, tex_dir)
            except Exception as e:
                print(f"Failed to move {img_file}: {e}")

move_obj_textures(export_paths["obj"])

print("导出完成！")
