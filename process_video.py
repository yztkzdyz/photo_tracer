import argparse
import os

import cv2
import numpy as np
import openvino as ov
from tqdm import tqdm


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="输入视频路径")
    parser.add_argument("--output", default="", help="输出视频路径（默认 output/<名字>_depth.mp4）")
    parser.add_argument("--model", default="models/depth_anything_v2_small.onnx", help="深度模型路径")
    parser.add_argument("--device", default="GPU", help="GPU / AUTO / CPU")
    parser.add_argument("--size", type=int, default=518, help="推理分辨率（14 的倍数效果最好）")
    parser.add_argument("--max-frames", type=int, default=0, help="只处理前 N 帧（0=全部），用于快速测试")
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.input)
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频: {args.input}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if args.max_frames > 0:
        total = min(total, args.max_frames)
    print(f"视频: {w}x{h} @ {fps:.2f}fps, 共 {total} 帧")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    if not args.output:
        stem = os.path.splitext(os.path.basename(args.input))[0]
        args.output = os.path.join("output", f"{stem}_depth.mp4")

    # mp4 优先，写不了就退回 avi
    writer = cv2.VideoWriter(args.output, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    if not writer.isOpened():
        alt = os.path.splitext(args.output)[0] + ".avi"
        print(f"mp4 编码器不可用，改写 {alt}")
        writer = cv2.VideoWriter(alt, cv2.VideoWriter_fourcc(*"XVID"), fps, (w, h))
        args.output = alt
    if not writer.isOpened():
        raise RuntimeError("无法创建输出视频文件")

    core = ov.Core()
    print("OpenVINO 可用设备:", core.available_devices)
    device = args.device
    if device not in core.available_devices and device != "AUTO":
        print(f"设备 {device} 不可用，回退到 AUTO")
        device = "AUTO"
    compiled = core.compile_model(core.read_model(args.model), device)
    input_port = compiled.input(0)
    output_port = compiled.output(0)

    from generate_depth import preprocess

    n = 0
    with tqdm(total=total or None, unit="帧", desc="深度处理") as bar:
        while n < total or total == 0:
            ok, frame = cap.read()
            if not ok:
                break
            result = compiled({input_port: preprocess(frame, args.size)})
            depth = np.squeeze(result[output_port]).astype(np.float32)
            depth = (depth - depth.min()) / (depth.max() - depth.min() + 1e-8)
            depth = cv2.resize(depth, (w, h), interpolation=cv2.INTER_LINEAR)
            d8 = np.clip(depth * 255.0, 0, 255).astype(np.uint8)
            writer.write(cv2.applyColorMap(d8, cv2.COLORMAP_TURBO))
            n += 1
            bar.update(1)

    cap.release()
    writer.release()
    print(f"完成: 共处理 {n} 帧, 已保存 {args.output}")


if __name__ == "__main__":
    main()
