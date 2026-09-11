import cv2
import numpy as np


def overlay_image(frame, overlay, x, y, scale, angle, alpha):
    h, w = overlay.shape[:2]
    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))

    resized = cv2.resize(overlay, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    M = cv2.getRotationMatrix2D((new_w / 2, new_h / 2), angle, 1)
    rotated = cv2.warpAffine(
        resized,
        M,
        (new_w, new_h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )

    fh, fw = frame.shape[:2]
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(fw, x + new_w), min(fh, y + new_h)

    if x1 >= x2 or y1 >= y2:
        return frame

    ox1, oy1 = x1 - x, y1 - y
    ox2, oy2 = ox1 + (x2 - x1), oy1 + (y2 - y1)

    roi = frame[y1:y2, x1:x2]
    ov = rotated[oy1:oy2, ox1:ox2]

    a = ov[:, :, 3:4] / 255.0 * alpha
    roi[:] = (1 - a) * roi + a * ov[:, :, :3]

    return frame


def main():
    overlay = cv2.imread("output/outline.png", cv2.IMREAD_UNCHANGED)
    if overlay is None:
        raise FileNotFoundError("找不到 output/outline.png，请先生成轮廓图。")

    if overlay.ndim == 2 or overlay.shape[2] == 3:
        overlay = cv2.cvtColor(overlay, cv2.COLOR_BGR2BGRA)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("无法打开摄像头")

    x, y, scale, angle, alpha = 100, 100, 1.0, 0, 0.5

    print("按键说明：")
    print("w/s 上下移动，a/d 左右移动")
    print("+/- 缩放，q/e 旋转")
    print("[ ] 调整透明度")
    print("p 保存截图，ESC 退出")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = overlay_image(frame, overlay, x, y, scale, angle, alpha)
        cv2.imshow("Camera Overlay", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break
        elif key == ord("w"):
            y -= 5
        elif key == ord("s"):
            y += 5
        elif key == ord("a"):
            x -= 5
        elif key == ord("d"):
            x += 5
        elif key in (ord("+"), ord("=")):
            scale *= 1.05
        elif key == ord("-"):
            scale /= 1.05
        elif key == ord("q"):
            angle += 2
        elif key == ord("e"):
            angle -= 2
        elif key == ord("["):
            alpha = max(0.0, alpha - 0.05)
        elif key == ord("]"):
            alpha = min(1.0, alpha + 0.05)
        elif key == ord("p"):
            cv2.imwrite("output/camera_snapshot.png", frame)
            print("已保存 output/camera_snapshot.png")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
