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


def subject_edges(image, model_path, device, threshold=0.5, line_width=3):
    """用 U-2-Net 分割人物主体，返回主体边界线（0/255 uint8，与原图同尺寸）。"""
    from generate_outline import postprocess, preprocess

    core = ov.Core()
    if device not in core.available_devices and device != "AUTO":
        device = "AUTO"
    compiled = core.compile_model(core.read_model(model_path), device)
    result = compiled({compiled.input(0): preprocess(image)})
    mask = postprocess(result[compiled.output(0)], image.shape)
    binary = (mask > threshold).astype(np.uint8) * 255
    edges = cv2.Canny(binary, 50, 150)
    kernel = np.ones((line_width, line_width), np.uint8)
    return cv2.dilate(edges, kernel, iterations=1)


def draw_edges_on_bgr(bgr, edges, color=(255, 255, 255)):
    out = bgr.copy()
    out[edges > 0] = color
    return out


def preprocess(image, size=518):
    # Depth Anything 期望 RGB, /255, (x-0.5)/0.5
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (size, size), interpolation=cv2.INTER_LINEAR)
    img = img.astype(np.float32) / 255.0
    img = (img - 0.5) / 0.5
    img = img.transpose(2, 0, 1)[None, ...]
    return np.ascontiguousarray(img.astype(np.float32))


def estimate_depth(image, compiled, input_port, output_port, size=518):
    h, w = image.shape[:2]
    result = compiled({input_port: preprocess(image, size)})
    depth = np.squeeze(result[output_port]).astype(np.float32)
    depth = (depth - depth.min()) / (depth.max() - depth.min() + 1e-8)
    depth = cv2.resize(depth, (w, h), interpolation=cv2.INTER_LINEAR)
    return depth  # 0=远, 1=近


def save_color_depth(depth, path):
    d8 = np.clip(depth * 255.0, 0, 255).astype(np.uint8)
    colored = cv2.applyColorMap(d8, cv2.COLORMAP_TURBO)
    imwrite_unicode(path, colored)


def save_isolines(depth, path, bands=8, edges=None):
    """等深线：把深度分成 bands 层，画层间边界。
    越近的等深线越粗、越不透明，颜色取自 turbo 伪彩色。
    edges 可选：叠加的主体轮廓线（白色、不透明，最上层）。"""
    h, w = depth.shape
    smooth = cv2.GaussianBlur(depth, (0, 0), sigmaX=min(h, w) / 200.0)

    band_idx = np.clip((smooth * bands).astype(np.int32), 0, bands - 1)
    edge = np.zeros((h, w), dtype=bool)
    edge[1:, :] |= band_idx[1:, :] != band_idx[:-1, :]
    edge[:, 1:] |= band_idx[:, 1:] != band_idx[:, :-1]

    colored = cv2.applyColorMap(np.clip(smooth * 255, 0, 255).astype(np.uint8), cv2.COLORMAP_TURBO)

    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    alpha = np.zeros((h, w), dtype=np.uint8)

    near = edge & (smooth > 0.66)
    mid = edge & (smooth > 0.33) & (smooth <= 0.66)
    far = edge & (smooth <= 0.33)

    # 近处线最粗（膨胀 2 次），中间 1 次，远处保持细线
    for mask, iters, base_alpha in [(near, 2, 230), (mid, 1, 170), (far, 0, 120)]:
        if not mask.any():
            continue
        m = (mask.astype(np.uint8)) * 255
        if iters > 0:
            m = cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=iters)
        mask = m > 0
        alpha[mask] = base_alpha

    rgba[:, :, :3] = colored
    rgba[:, :, 3] = alpha

    if edges is not None:
        rgba[edges > 0] = [255, 255, 255, 255]

    imwrite_unicode(path, rgba)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="输入图片路径")
    parser.add_argument("--output-dir", default="output", help="输出目录")
    parser.add_argument("--model", default="models/depth_anything_v2_small.onnx", help="深度模型路径")
    parser.add_argument("--device", default="GPU", help="GPU / AUTO / CPU")
    parser.add_argument("--size", type=int, default=518, help="推理分辨率（14 的倍数效果最好）")
    parser.add_argument("--bands", type=int, default=8, help="等深线层数")
    parser.add_argument("--mode", choices=["all", "color", "isolines"], default="all")
    parser.add_argument("--subject-outline", action="store_true",
                        help="用 U-2-Net 提取人物主体轮廓并叠加到输出上")
    parser.add_argument("--u2net-model", default="models/u2net.onnx", help="U-2-Net 模型路径")
    parser.add_argument("--line-width", type=int, default=3, help="主体轮廓线宽")
    args = parser.parse_args()

    image = imread_unicode(args.input, cv2.IMREAD_COLOR)
    os.makedirs(args.output_dir, exist_ok=True)

    core = ov.Core()
    print("OpenVINO 可用设备:", core.available_devices)
    device = args.device
    if device not in core.available_devices and device != "AUTO":
        print(f"设备 {device} 不可用，回退到 AUTO")
        device = "AUTO"

    compiled = core.compile_model(core.read_model(args.model), device)
    input_port = compiled.input(0)
    output_port = compiled.output(0)

    depth = estimate_depth(image, compiled, input_port, output_port, args.size)

    edges = None
    suffix = ""
    if args.subject_outline:
        edges = subject_edges(image, args.u2net_model, args.device, line_width=args.line_width)
        suffix = "_subject"

    stem = os.path.splitext(os.path.basename(args.input))[0]
    if args.mode in ("all", "color"):
        path = os.path.join(args.output_dir, f"{stem}_depth{suffix}.png")
        colored = cv2.applyColorMap(np.clip(depth * 255, 0, 255).astype(np.uint8), cv2.COLORMAP_TURBO)
        if edges is not None:
            colored = draw_edges_on_bgr(colored, edges)
        imwrite_unicode(path, colored)
        print(f"已保存伪彩色深度图: {path}")
    if args.mode in ("all", "isolines"):
        path = os.path.join(args.output_dir, f"{stem}_depth_isolines{suffix}.png")
        save_isolines(depth, path, args.bands, edges=edges)
        print(f"已保存深度分层等深线: {path}")


if __name__ == "__main__":
    main()
