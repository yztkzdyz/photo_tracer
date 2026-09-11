import numpy as np
import cv2
from camera_overlay import overlay_image

# 合成帧：640x480 蓝色背景
frame = np.full((480, 640, 3), (200, 100, 0), dtype=np.uint8)
# 合成叠加图：100x100 红色方块，带 alpha 通道
ov = np.zeros((100, 100, 4), dtype=np.uint8)
ov[:, :, 2] = 255  # 红色
ov[:, :, 3] = 255  # 不透明

# 1) 基本叠加（alpha=0.5 -> 混合色）
frame1 = overlay_image(frame.copy(), ov, 10, 10, 1.0, 0, 0.5)
# 中心点应混入 50% 红色
b, g, r = frame1[60, 60]
assert r > 120 and b < 110, f"混合颜色不对: {b},{g},{r}"
print(f"1) 基本叠加 OK（混合像素 BGR={b},{g},{r}）")

# 2) 缩放
frame2 = overlay_image(frame.copy(), ov, 0, 0, 2.0, 0, 1.0)
assert frame2[150, 150, 2] == 255, "2 倍缩放后 150,150 应为红色"
assert frame2[230, 230, 2] < 255, "缩放外区域不应被覆盖"
print("2) 缩放 OK")

# 3) 旋转 45 度（中心仍在叠加区域）
frame3 = overlay_image(frame.copy(), ov, 100, 100, 1.0, 45, 1.0)
assert frame3[150, 150, 2] == 255, "旋转中心应保持红色"
print("3) 旋转 OK")

# 4) 越界裁剪（负坐标放置不崩溃）
frame4 = overlay_image(frame.copy(), ov, -50, -50, 1.0, 0, 1.0)
print("4) 越界放置 OK（无崩溃）")

# 5) 摄像头可用性
cap = cv2.VideoCapture(0)
opened = cap.isOpened()
if opened:
    ret, cam_frame = cap.read()
    print(f"5) 摄像头 0 可打开，读帧成功: {ret}, 尺寸: {None if cam_frame is None else cam_frame.shape}")
else:
    print("5) 摄像头 0 不可用（GUI 脚本运行时会报错并需要换索引或接摄像头）")
cap.release()
