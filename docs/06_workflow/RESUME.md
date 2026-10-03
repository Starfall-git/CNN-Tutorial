# 恢复工作记录

2026-10-04：按用户要求，在短期额度剩余约 3% 时开始保存并停止，防止最后的提交耗尽额度。阶段编号必须在后续交付中明确说明。

## 已完成并合并

- 阶段 1：用户在 MAIN 勾选，PR #1 已合并。
- 阶段 2/3：训练验证与一次分组优化技术工作完成，用户授权完成当前工作后合并，PR #2 已合并。MAIN 阶段 2/3 的勾选仍由用户确认。
- 远端 main 为 `0172385c5de67b6044e5fcd5f22a341aafafad0a`，两个 PR 的 CI 均通过。
- 最终模型：26,371 参数、10,030,080 MACs；公开回顾性基准 accuracy 95.70%，macro-F1 0.9563，paper recall 87.10%。真实相机和背景拒识未验证。
- 权重：`artifacts/v0.2-grouped-study/refit/best.pt`，SHA-256 `ed3e422f75b1765953cddc91fd49ab0f140e43f5c2c72e2a69785930365972ad`。

## 阶段 4 已做的准备

- 当前工作分支 `feat/v0.3-int8-export`，从已合并 main 开始。
- 独立 conda 环境 `CNN-Tutorial-Quant` 已创建，Python 3.11.16；**TensorFlow 尚未安装**。原训练环境保持 PyTorch CUDA。
- `scripts/prepare_conversion.py` 已实际运行，生成 `artifacts/v0.3-conversion-input/`。
- `weights.npz` 是冻结权重；`calibration.npz` 为训练池中每类 100 张，共 300 张；`evaluation.npz` 为 372 张官方测试图、标签与 PyTorch logits。校准/评估内容哈希不交叉。
- manifest 保存上述文件与模型摘要。转换输入不得混用其他 checkpoint。
- `scripts/convert_int8.py` 仅通过语法编译，**尚未执行/验证**。包含 Conv OIHW→HWIO、Dense CHW→HWC 权重重排、浮点一致性断言、全 INT8 转换和测试报告。当前不存在已验证的 `.tflite` 产物。

## 恢复后的顺序

1. 先检查账号用量；用户要求额度恢复再继续，不购买额外额度、不消耗重置权益。
2. 核对 git 状态、当前分支、PR 和本地 artifacts；不要重复下载数据或重训已经冻结的模型。
3. 在 `CNN-Tutorial-Quant` 中执行 `python -m pip install -r requirements-quant.txt`。锁定 TensorFlow 2.15.1、NumPy 1.26.4；Windows 使用 CPU 转换。网络代理对部分站点发生 TLS EOF，先核查连接，不关闭证书验证。
4. 执行 `python scripts/convert_int8.py`，修复实际错误。验证 FP32 logits 一致、INT8 I/O、无浮点张量、真实校准、同一测试集精度下降 ≤2 个百分点。还应补充 FlatBuffer 算子版本审计、模型元数据和 golden 输入输出，不能把桌面 interpreter 成功当作板卡兼容。
5. 增加 Notebook 04 与量化文档，使用真实输出；更新阶段 4 的完成/未完成边界。提交 PR 和检查。
6. 阶段 5/6 仍缺用户现有 FPGA 工程、准确板卡/工具版本与板端实测，不能宣称完成；阶段 7 的第二个模型仍未搭建。

## 其他状态

- Code Review 插件仍返回无法连接 GitHub；GitHub 连接器可正常读写、查询 CI。不得声称插件审查通过。
- Jupyter 服务在本机 8889；已有 d2l 服务在 8888，保持不动。暂停前没有仍在运行的训练或依赖安装任务。
- Notebook 00 的 kernel 名称由 Jupyter 保存为小写 `cnn-tutorial`，已保留该变更。
