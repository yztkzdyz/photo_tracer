# photo_tracer — 本地照片复刻辅助工具

用 Intel 核显（OpenVINO）跑 U-2-Net 主体分割，生成半透明轮廓图 / 半透明主体图 / 二值掩膜，
再把半透明 PNG 叠加到摄像头画面上，手动移动、缩放、旋转、调透明度，辅助复刻构图。

## 环境要求

- Windows 10/11，Python 3.10+
- Intel 核显（Iris Xe 等）+ OpenVINO（设备优先 GPU，失败自动回退 AUTO/CPU）

## 首次使用

```powershell
cd photo_tracer   # 进入项目目录（GitHub 上 clone 后的位置）
.\.venv\Scripts\Activate.ps1
# 如果提示禁止激活脚本，先执行：
# Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

python -m venv .venv                          # 首次使用先建虚拟环境
python -m pip install -r requirements.txt     # 安装依赖
python download_model.py                      # 下载 u2net.onnx（约 168MB，带进度条）
python download_depth_model.py                # （可选）下载深度模型（约 94MB）
python make_bats.py                           # （可选）重新生成双击可用的 bat 脚本
python fetch_test_image.py                    # （可选）下载一张示例图片到 input/test.jpg
```

Windows 下也可以直接双击 `处理图片.bat`（把照片拖到图标上）和 `摄像头叠加.bat` 使用，
不需要手动激活虚拟环境。bat 是 GBK 编码，改动后用 `make_bats.py` 重新生成。

## 生成叠加素材

把你的参考图放到 `input\`，然后：

```powershell
# 半透明轮廓图（透明背景白线）
python generate_outline.py --input input\test.jpg --output output\outline.png --mode outline --device GPU

# 线稿风格（含五官、发丝、衣褶等内部细节，铅笔灰黑色线条，透明背景）
python generate_outline.py --input input\test.jpg --output output\lineart.png --mode lineart --device GPU
# --detail 数值越小线条越多越碎（默认 7，奇数）

# 半透明主体图（保留原图颜色，主体区域半透明）
python generate_outline.py --input input\test.jpg --output output\overlay.png --mode overlay --opacity 0.5 --device GPU

# 二值掩膜
python generate_outline.py --input input\test.jpg --output output\mask.png --mode mask --device GPU
```

常用参数：

- `--threshold 0.4~0.7`：主体识别阈值，识别不准时调整
- `--line-width 1~3`：轮廓线粗细
- `--opacity 0.0~1.0`：半透明主体图的不透明度
- `--device GPU / AUTO / CPU`：GPU 报错时改用 AUTO 或 CPU

如果 OpenVINO 读 ONNX 失败，先 `pip install onnx`；仍失败可转 IR：

```powershell
python -c "import openvino as ov; core=ov.Core(); m=core.read_model('models/u2net.onnx'); ov.save_model(m,'models/u2net.xml')"
# 之后加参数 --model models/u2net.xml
```

## 生成深度图（可选）

基于 Depth Anything V2 small（单目深度估计，相对深度：近处暖色/粗线，远处冷色/细线），
同样走核显 GPU。首次使用先下载模型（约 94MB）：

```powershell
python download_depth_model.py
```

生成两种输出（自动以输入文件名命名）：

```powershell
python generate_depth.py --input input\test.jpg --device GPU
# -> output\test_depth.png            伪彩色深度图（turbo：红=近，蓝=远）
# -> output\test_depth_isolines.png   深度分层等深线（透明背景，近粗远细，可叠加）
```

参数：`--bands 8`（等深线层数）、`--size 518`（推理分辨率，14 的倍数）、`--mode color/isolines/all`。

加 `--subject-outline` 可用 U-2-Net 提取人物主体轮廓（白线）叠加到两种深度图上，
文件名会带 `_subject` 后缀，例如 `test_depth_subject.png`；`--line-width 3` 控制轮廓线宽。

注意：单目深度是相对深度（谁近谁远），不能当绝对距离测量用。

## 摄像头叠加

```powershell
python camera_overlay.py
```

先确保 `output/outline.png` 已生成。按键说明：

| 按键 | 功能 |
| --- | --- |
| w / s / a / d | 上 / 下 / 左 / 右移动 |
| + / - | 缩放 |
| q / e | 旋转 |
| [ / ] | 降低 / 提高透明度 |
| p | 保存截图到 output/camera_snapshot.png |
| ESC | 退出 |

摄像头打不开时，把 `camera_overlay.py` 里的 `cv2.VideoCapture(0)` 改成 `cv2.VideoCapture(1)`。

## 目录结构

```
photo_tracer/
  .venv/               Python 虚拟环境
  models/              u2net.onnx 模型
  input/               参考图片（放入你的照片）
  output/              生成的轮廓图 / 主体图 / 掩膜 / 截图
  requirements.txt     依赖清单
  download_model.py    下载 U-2-Net 模型（带进度条）
  download_depth_model.py 下载 Depth Anything V2 深度模型
  generate_depth.py    生成伪彩色深度图 / 深度分层等深线
  fetch_test_image.py  下载示例测试图
  generate_outline.py  生成轮廓 / 主体 / 掩膜
  camera_overlay.py    摄像头叠加辅助
```
