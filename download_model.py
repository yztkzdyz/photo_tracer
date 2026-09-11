import os
import requests
from tqdm import tqdm

MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

urls = [
    "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx",
    "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx",
]

target = os.path.join(MODEL_DIR, "u2net.onnx")

for url in urls:
    try:
        print(f"尝试下载: {url}")
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with open(target, "wb") as f, tqdm(
            total=total, unit="B", unit_scale=True, unit_divisor=1024, desc="u2net.onnx"
        ) as bar:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))
        print(f"下载完成: {target} ({os.path.getsize(target) / 1024 / 1024:.1f} MB)")
        break
    except Exception as e:
        print(f"下载失败: {e}")
else:
    print("所有下载地址都失败，请手动下载 u2net.onnx 并放到 models/ 目录。")
