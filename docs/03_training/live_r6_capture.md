# r5 上板反馈后的实拍采集准备

r5 已在 Ti60 实时运行，但用户在复杂背景中观察到剪刀、布和空场景识别问题。公开合成 RPS 测试集的 95% 左右准确率不能代表 AR0135 实拍。此页面记录原三类项目的四类实验准备：`paper, rock, scissors, empty`。五种新手势的原图检测实验另放桌面 `CNN-Tutorial-Gesture`，两者不要混用标签或权重。

## 采集原则

用现有 `CNN-Tutorial-FPGA` r5 视频链路和 Hagibis HDMI 采集卡。关闭原上位机 GUI，释放 COM8 和采集设备；板卡保持 `.bit` 与 RISC-V 固件运行。脚本先检查 100% 未翻转/未裁剪几何以及关闭的 ISP，临时关闭 AI 推理与叠加，再保存完整 1280×720 帧和精确对应硬件 `512×512` ROI、`8` 倍抽样的 64×64 灰度输入。结束后恢复原 AI 开关。HDMI-UVC-MJPEG 帧是板端输入的近似回放，不能视为逐字节一致的 RAW8。

每次会话包含四类，并尽量改变人物、背景、光线和手距。`empty` 分成无手背景 `--empty-kind background` 与非目标手势 `--empty-kind other_hand`；两者都应采。每个会话中的连续帧只能进入同一个训练/验证/测试分区，避免帧泄漏。源图片留在忽略的 `data/live_r6/`，不要提交原始室内影像到 GitHub。

```powershell
python scripts/capture_live_roi.py --session roomA_day --label rock --count 40
python scripts/capture_live_roi.py --session roomA_day --label scissors --count 40
python scripts/capture_live_roi.py --session roomA_day --label paper --count 40
python scripts/capture_live_roi.py --session roomA_day --label empty --empty-kind background --count 20
python scripts/capture_live_roi.py --session roomA_day --label empty --empty-kind other_hand --count 20
```

至少安排一个训练会话、一个验证会话、一个从未调参使用的测试会话。建议训练使用多个不同的人/背景会话。创建 JSON 如 `data/live_r6/splits.json`，内容示例：

```json
{"train":["roomA_day","roomB_night"],"val":["roomC_day"],"test":["roomD_night"]}
```

```powershell
python scripts/build_live_manifest.py --assignments data/live_r6/splits.json
python scripts/train_live.py --epochs 30
```

训练脚本可只重用原三类 CNN 的卷积特征，四类输出层重新初始化。验证集选模；测试集仅在选定模型后运行一次。新模型如需上板，仍要重新 INT8 量化、算子审计和三向量/动态输入复验，不会自动替换 r5 固件。
