import cv2
import numpy as np

outline = cv2.imread("output/outline.png", cv2.IMREAD_UNCHANGED)
overlay = cv2.imread("output/overlay.png", cv2.IMREAD_UNCHANGED)
mask = cv2.imread("output/mask.png", cv2.IMREAD_UNCHANGED)

for name, img, expect in [
    ("outline", outline, 4),
    ("overlay", overlay, 4),
    ("mask", mask, 1),
]:
    assert img is not None, f"{name} 未生成"
    ch = 1 if img.ndim == 2 else img.shape[2]
    assert ch == expect, f"{name} 通道数 {ch} != 期望 {expect}"
    print(f"{name}: shape={img.shape} OK")

# outline: 透明背景 + 白色不透明线条
alpha = outline[:, :, 3]
print(f"outline 透明像素占比: {(alpha == 0).mean() * 100:.1f}%")
assert (alpha == 0).mean() > 0.3, "outline 透明背景占比过低"
lines = outline[alpha > 0]
assert np.all(lines[:, :3] == 255), "outline 线条不是纯白"
print("outline: 透明背景 + 纯白线条 OK")

# overlay: 主体区域半透明（alpha 约为 128），背景全透明
oa = overlay[:, :, 3]
vals = np.unique(oa)
print(f"overlay alpha 取值: {vals}")
assert ((oa == 0) | (oa == 127) | (oa == 128)).all(), "overlay alpha 不是 0/128 两档"
print(f"overlay 主体区域占比: {((oa == 127) | (oa == 128)).mean() * 100:.1f}%")
print("overlay: 半透明主体 OK")

# mask: 只含 0/255
assert set(np.unique(mask)).issubset({0, 255}), "mask 不是二值图"
print(f"mask 主体占比: {(mask == 255).mean() * 100:.1f}%")
print("mask: 二值掩膜 OK")
