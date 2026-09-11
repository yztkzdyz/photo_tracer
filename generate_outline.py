import argparse
import os

import cv2
import numpy as np
import openvino as ov


def imread_unicode(path, flags=cv2.IMREAD_COLOR):
    """cv2.imread 在 Windows 上读不了含中文的路径，改用字节流解码。"""
    data = np.fromfile(path, dtype=np.uint8)
    img = cv2.imdecode(data, flags)
    if img is None:
        raise FileNotFoundError(f"无法读取图片: {path}")
    return img


def imwrite_unicode(path, img):
    """cv2.imwrite 在 Windows 上写不了含中文的路径，改用字节流编码。"""
    ext = os.path.splitext(path)[1] or ".png"
    ok, buf = cv2.imencode(ext, img)
    if ok:
        buf.tofile(path)
    return ok


def preprocess(image, size=320):
    img = cv2.resize(image, (size, size))
    img = img.astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img = (img - mean) / std
    img = img.transpose(2, 0, 1)[None, ...]
    return img.astype(np.float32)


def postprocess(pred, original_shape):
    pred = np.squeeze(pred)
    pred = (pred - pred.min()) / (pred.max() - pred.min() + 1e-8)
    mask = cv2.resize(pred, (original_shape[1], original_shape[0]))
    return mask


def sketch_lines(image, keep_mask, detail=7, min_strength=30):
    """提取铅笔线稿风格的线条（含五官、发丝、衣褶等内部细节）。
    keep_mask 限定只保留主体内的线条。返回 0-255 线条深浅图，越大线越深。
    detail 为自适应阈值的邻域大小（奇数），越小细节越多。"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    white_bg = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, detail, 2
    )
    lines = 255 - white_bg  # 黑线转正
    lines[lines < min_strength] = 0
    lines[keep_mask == 0] = 0
    return lines


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="输入图片路径")
    parser.add_argument("--output", default="output/outline.png", help="输出 PNG 路径")
    parser.add_argument("--model", default="models/u2net.onnx", help="U-2-Net ONNX 模型路径")
    parser.add_argument("--mode", choices=["outline", "overlay", "mask", "lineart"], default="outline")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--line-width", type=int, default=2)
    parser.add_argument("--opacity", type=float, default=0.5)
    parser.add_argument("--device", default="GPU", help="GPU / AUTO / CPU")
    parser.add_argument("--detail", type=float, default=6.0,
                        help="lineart 模式：线条细节尺度，越小线条越多越碎，越大越简洁")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    core = ov.Core()
    print("OpenVINO 可用设备:", core.available_devices)

    device = args.device
    if device not in core.available_devices and device != "AUTO":
        print(f"设备 {device} 不可用，回退到 AUTO")
        device = "AUTO"

    model = core.read_model(args.model)
    compiled = core.compile_model(model, device)

    input_port = compiled.input(0)
    output_port = compiled.output(0)

    original = imread_unicode(args.input, cv2.IMREAD_COLOR)

    h, w = original.shape[:2]
    input_tensor = preprocess(original)

    result = compiled({input_port: input_tensor})
    pred = result[output_port]
    mask = postprocess(pred, original.shape)

    binary = (mask > args.threshold).astype(np.uint8) * 255

    if args.mode == "mask":
        imwrite_unicode(args.output, binary)
        print(f"已保存掩膜: {args.output}")
        return

    kernel = np.ones((args.line_width, args.line_width), np.uint8)
    edges = cv2.Canny(binary, 50, 150)
    edges = cv2.dilate(edges, kernel, iterations=1)

    rgba = np.zeros((h, w, 4), dtype=np.uint8)

    if args.mode == "outline":
        rgba[edges > 0] = [255, 255, 255, 255]
    elif args.mode == "overlay":
        rgba[:, :, :3] = original
        alpha = (binary.astype(np.float32) * args.opacity).astype(np.uint8)
        rgba[:, :, 3] = alpha
    elif args.mode == "lineart":
        # 线稿：主体内部的细节线条 + 外轮廓，线条用铅笔灰黑色，alpha 随线条深浅变化
        keep = cv2.dilate(binary, np.ones((args.line_width * 2 + 1, args.line_width * 2 + 1), np.uint8))
        detail = max(3, int(args.detail) | 1)  # 保证奇数
        lines = sketch_lines(original, keep, detail=detail)
        lines = np.maximum(lines, edges)  # 外轮廓保证完整
        rgba[:, :, 0] = 30
        rgba[:, :, 1] = 30
        rgba[:, :, 2] = 30
        rgba[:, :, 3] = lines

    imwrite_unicode(args.output, rgba)
    print(f"已保存: {args.output}")


if __name__ == "__main__":
    main()
