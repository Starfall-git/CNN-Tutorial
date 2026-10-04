# 恢复工作记录

2026-10-04：用户恢复执行后额度已恢复，阶段 4 的桌面量化验证已完成。后续交付继续明确阶段编号，接近额度阈值先保存再停止。

## 已完成并合并

- 阶段 1：用户在 MAIN 勾选，PR #1 已合并。
- 阶段 2/3：训练验证与一次分组优化技术工作完成，用户授权完成当前工作后合并，PR #2 已合并。MAIN 阶段 2/3 的勾选仍由用户确认。
- 远端 main 为 `0172385c5de67b6044e5fcd5f22a341aafafad0a`，两个 PR 的 CI 均通过。
- 最终模型：26,371 参数、10,030,080 MACs；公开回顾性基准 accuracy 95.70%，macro-F1 0.9563，paper recall 87.10%。真实相机和背景拒识未验证。
- 权重：`artifacts/v0.2-grouped-study/refit/best.pt`，SHA-256 `ed3e422f75b1765953cddc91fd49ab0f140e43f5c2c72e2a69785930365972ad`。

## 阶段 4 本轮完成

- 当前工作分支 `feat/v0.3-int8-export`，从已合并 main 开始。
- 独立环境 `CNN-Tutorial-Quant`：Python 3.11.16、TensorFlow 2.15.1、NumPy 1.26.4 已安装，`pip check` 通过。原训练环境保持 PyTorch CUDA。
- `scripts/prepare_conversion.py` 已实际运行，生成 `artifacts/v0.3-conversion-input/`。
- `weights.npz` 是冻结权重；`calibration.npz` 为训练池中每类 100 张，共 300 张；`evaluation.npz` 为 372 张官方测试图、标签与 PyTorch logits。校准/评估内容哈希不交叉。
- manifest 保存上述文件与模型摘要。转换输入不得混用其他 checkpoint。
- `scripts/convert_int8.py` 已实际执行：FP32 最大误差 1.049e-5，类别完全一致；INT8 accuracy 95.43%，下降 0.2688 个百分点，macro-F1 0.9535，33,240 字节。
- `artifacts/v0.3-int8/gesture_int8.tflite` SHA-256：`7891518a9b70ec6b3be8649123651780ce87ede1e69a9a49c394c17d203a0baa`。
- FlatBuffer 审计：14 个 INT8、5 个 INT32 张量，无 float/custom ops。三组 golden 向量已独立逐字节回放通过。
- 随 refs 提供的厂商 `tflite.exe` 返回 0，识别 Conv/FC；1/1 仅为分析探测参数，没有生成硬件配置，没有板端验证。
- Notebook 04 已在真实 Jupyter kernel 执行。报告、算子审计、哈希与环境快照归档于 `docs/05_experiments/v0.3/`，二进制留在本地 artifacts。

## 恢复后的顺序

1. 先检查账号用量；用户要求额度恢复再继续，不购买额外额度、不消耗重置权益。
2. 核对 git 状态、当前分支、PR 和本地 artifacts；不要重复下载数据或重训已经冻结的模型。
3. 核对本轮 PR #3 的最新提交、CI 和阶段确认。按用户约定处理确认后的合并，不自行勾选阶段。
4. 下一步是阶段 5。已请求用户提供 FPGA 工程路径、准确器件与 Efinity/RISC-V IDE 版本；收到工程后核查 AXI/DDR、时钟、资源、TFLite Micro 版本与算子注册。
5. 先用 golden 输入对齐目标 runtime 的输出字节/argmax，测 arena，再接 64×64 灰度 ROI。相机数据位深、黑电平、resize 坐标和舍入需明确对齐。
6. 阶段 6 实测连续视频、HDMI 叠加与端到端 FPS；阶段 7 第二模型保持用户给出的后续顺序。整个目标尚未完成。

## 其他状态

- Code Review 插件仍返回无法连接 GitHub；GitHub 连接器可正常读写、查询 CI。不得声称插件审查通过。
- Jupyter 服务在本机 8889；已有 d2l 服务在 8888，保持不动。暂停前没有仍在运行的训练或依赖安装任务。
- Notebook 00 的 kernel 名称由 Jupyter 保存为小写 `cnn-tutorial`，已保留该变更。
