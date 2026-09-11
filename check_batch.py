import cv2
import numpy as np

for i in range(1, 6):
    src = cv2.imread(f"input/p{i}.jpg")
    out = cv2.imread(f"output/outline_p{i}.png", cv2.IMREAD_UNCHANGED)
    assert out is not None, f"outline_p{i}.png 读取失败"
    assert out.shape[2] == 4, f"outline_p{i} 不是 RGBA"
    alpha = out[:, :, 3]
    line_pct = (alpha > 0).mean() * 100
    print(
        f"p{i}: 原图 {src.shape[1]}x{src.shape[0]}, "
        f"轮廓像素占比 {line_pct:.2f}%, 透明背景 {100 - line_pct:.1f}%"
    )
print("全部检查通过")
