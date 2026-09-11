import os

import requests
from tqdm import tqdm

MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

# Depth Anything V2 small（单目深度估计，ONNX）
# 主源 hf-mirror.com（国内镜像），备用 huggingface.co 直连
urls = [
    "https://hf-mirror.com/onnx-community/depth-anything-v2-small/resolve/main/onnx/model.onnx",
    "https://huggingface.co/onnx-community/depth-anything-v2-small/resolve/main/onnx/model.onnx",
    "https://hf-mirror.com/Xenova/depth-anything-small-hf/resolve/main/onnx/model_quantized.onnx",
]

target = os.path.join(MODEL_DIR, "depth_anything_v2_small.onnx")

if os.path.exists(target) and os.path.getsize(target) > 10 * 1024 * 1024:
    print(f"模型已存在，跳过下载: {target}")
else:
    for url in urls:
        try:
            print(f"尝试下载: {url}")
            r = requests.get(url, stream=True, timeout=60)
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            with open(target, "wb") as f, tqdm(
                total=total, unit="B", unit_scale=True, unit_divisor=1024, desc="depth.onnx"
            ) as bar:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))
            print(f"下载完成: {target} ({os.path.getsize(target) / 1024 / 1024:.1f} MB)")
            break
        except Exception as e:
            print(f"下载失败: {e}")
            if os.path.exists(target):
                os.remove(target)
    else:
        print("所有下载地址都失败，请手动下载 Depth Anything V2 small ONNX 放到 models/depth_anything_v2_small.onnx")
