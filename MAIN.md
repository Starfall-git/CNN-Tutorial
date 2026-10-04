# CNN-Tutorial · 版本、约束与阶段

当前版本：**v0.4.0 开发中：RISC-V 静态固件与 FPGA 接入**。GitHub：[Starfall-git/CNN-Tutorial](https://github.com/Starfall-git/CNN-Tutorial)（Private）。

用户已确认并勾选**阶段 1**；授权合并的 PR #1/#2 均已合并。阶段 2/3 的技术工作与结果已交付，清单仍等待用户确认；阶段 4 的桌面量化验证已完成，PR #3 已合并。当前完成阶段 5.3 的静态固件交叉编译，尚未完成上板运行。

最新实测：26,371 参数，FP32 accuracy **95.70%**；全整数 INT8 accuracy **95.43%**、macro-F1 **0.9535**，模型 **33,240 字节**。量化下降 **0.27 个百分点**。这是已被观察过的合成数据基准，真实摄像头、无手背景与 FPGA FPS 仍待验证。

**阶段勾选由用户确认；代理不自行勾选。** 下方保留原始需求与阶段清单。当前模型 1 已选择固定 ROI 的 64×64 灰度石头/剪刀/布分类。

## 当前实施约束

1. 使用已有 conda `CNN-Tutorial` 训练环境；框架版本与 GPU 以实测快照为准。
2. 板卡部署入口为全整数 INT8 `.tflite` + TinyML/TFLite Micro。PyTorch 文件、ONNX 或 PC 推理成功不等于板卡兼容。
3. 参数量、MACs、模型大小、tensor arena 和板上延迟分别报告。15 FPS 是待实测目标。
4. 使用原始灰度/彩色图像训练；Sobel 保持独立功能。首个模型优先复用 AR0135。
5. 验证集用于选模；最终测试不用来训练、调参或校准。公开数据成绩与实拍成绩分别记录。
6. 每段 notebook 代码前放 Markdown 说明，基础语法简表在末尾；Python 模块保存共享实现。
7. `refs/` 原始厂商资料、数据、大权重和运行凭证留在本地；Git 同步代码、教程与小体积实验报告。
8. 每个主要版本检查、commit、push、PR；阶段确认后同步 MAIN 勾选。首版保留 PR 供审阅。

## 文档与学习入口

| 主题 | 文件 |
|---|---|
| 环境与启动 | [环境说明](docs/01_setup/environment.md) |
| 模型与关键源码 | [灰度 CNN](docs/02_model/gray_gesture_cnn.md) |
| 数据、训练、验证与云端流程 | [训练说明](docs/03_training/data_and_evaluation.md) |
| 量化、板卡与摄像头约束 | [部署约定](docs/04_deployment/tinyml_contract.md) |
| INT8 转换与 golden 回放 | [量化教程](docs/04_deployment/int8_conversion.md) |
| FPGA 接入与独立副本 | [阶段 5 实施记录](docs/04_deployment/fpga_bringup.md) |
| RISC-V 静态固件 | [构建与关键源码](docs/04_deployment/riscv_static_firmware.md) |
| 自定义指令与缓存 | [CI 接口约定](docs/04_deployment/riscv_custom_instruction.md) |
| 真实实验记录 | [v0.1.0 基线](docs/05_experiments/v0.1.0_baseline.md) |
| 分组验证与优化记录 | [v0.2.0 实验](docs/05_experiments/v0.2/README.md) |
| 全整数精度与算子审计 | [v0.3.0 实验](docs/05_experiments/v0.3/README.md) |
| GitHub 与 Code Review | [版本工作流](docs/06_workflow/versioning.md) |

Notebook 顺序：[00 环境](notebooks/00_environment.ipynb) → [01 搭建](notebooks/01_gray_gesture_cnn.ipynb) → [02 训练验证](notebooks/02_train_validate.ipynb)。

优化进阶：[03 分组验证与最终训练](notebooks/03_grouped_optimization.ipynb)。默认回放真实实验记录；可切换为完整训练。

部署准备：[04 INT8 量化](notebooks/04_int8_quantization.ipynb)。默认回放真实量化报告；可切换为隔离环境导出。

---

## 原始需求与阶段清单

> 可以链接到.\docs\下的markdown文件去。

## 项目介绍与要求
### 项目主文件夹地址：C:\Users\SteLl1a\Desktop\CNN-Tutorial。

### 主要任务：

搭建、训练并验证两个分别基于CNN的物品识别(可考虑Detection)或手势识别(可考虑Image Classification)的较高准确度但参数量小的CNN模型（或其他神经网络模型），类似于小参数的YOLO模型比如yoloV3等（模型参数量不宜过大，最好能让后续部署到FPGA板卡时fps能达到15左右），使用jupyter notebook环境，我已经创建好conda环境“CNN-Tutorial"(python版本3.14.8，pytorch版本2.14.1支持计算平台CUDA13.2），你直接运行anaconda prompt进入激活该环境，使用jupyter notebook即可。最好基于pytorch或tensorflow（我们相对更熟悉一些，具体选择哪个，还得参考板子的TinyML介绍，模型量化工具等，能迁移部署到板卡上），能量化至INT8，方便我们后续部署至板子上，具体参考TinyML介绍和使用说明文件，这些参考文件我们也放到了.\refs\下。模型的搭建和训练可以参考ultralytics网站（YOLO模型训练平台）。本项目还要起教程的作用，参考d2l.ai。



### 项目格式化、可解释性与Workflow：

\- 关于搭建、训练、验证的步骤解释和部分关键源码解释，请编写markdown格式的文件，放至.\docs\下，不要杂糅在一起，要规范、格式化的整理放置在不同文件夹下并准确的命名。版本迭代与约束申明，在.\MAIN.md内，版本迭代可以具体链接到docs下的markdown文件。

\- 仿照d2l.ai教程风格，使用jupyter notebook, .ipynb和python来搭建神经网络的同时，使用markdown的cell作为每段python cell代码的解释。关于某些基本语法、基本函数使用的知识和简要解释等，可以放在notebook的末尾cells内。

\- 整个workflow参考GitHub，使用我的账户GitHub Starfall.taken@gmail.com创建一个CNN-Tutorial仓库，并进行标准但又简单的workflow（agent代理风格，简单的workflow，不宜太复杂消耗过多Tokens），对每次大版本迭代更新进行自动git commit, push , PR和仓库管理。Code Review 



### 阶段性目标：

- [x] 1. 先分步尝试搭建第一个模型（选择更简单的那一个，物品识别/手势识别），搭建时参考d2l.ai教程的风格来解释，但是不要解释的过多过详细也不要太浅显。

- [ ] 2. 训练并验证第一个模型，可以指导我使用网上平台与图片数据库（比如ultralytics的）进行训练

- [ ] 3. 优化模型（结构/框架/训练），迭代模型。

- [ ] 4. 模型量化，转INT8等。
- [ ] 5. 我将提供我们现在已完成的基于易灵思FPGA板卡的摄像头-DDR3-串口-上位机控制-图像处理（sobel边缘检测等）-HDMI输出的边缘检测图像处理系统的工程文件，里面包含板卡信息、所有开发调试记录、源码、工程文件等。根据tinyml用户手册，和我一起，step-by-step，尝试部署到板子上。模型的训练图片不需要经过边缘处理（网上这种训练数据库较少），可以是黑白的/彩色的。我们可以将神经网络的物品识别或手势识别其作为sobel边缘检测与显示系统之外的一项功能，即不用sobel边缘检测，原图采样直接进行推理。目前工程里我们的摄像头是黑白的720p的AR0135，我们也可以替换为OV5640彩色摄像头（可以到1080p），或mipi接口的其他彩色摄像头。关于具体选择黑白还是彩色的图片来训练和推理，可以提供给我们建议，我们根据建议来选择摄像头并修改图像处理系统，来保证神经网络模型的部署。
- [ ] 6. 模型成功部署到FPGA板卡，并能实时推理与原画（或经过边缘处理的图像）叠加显示。

- [ ] 7. 尝试搭建第二个模型。

- [ ] 8. ......（待后续添加）



其他备注：

1. 经过迭代，完成某个阶段性目标后，我会告知你，并在MAIN.md内将其勾选上，你要将该版本项目文件PR并同步到GitHub仓库里。



[Dive into Deep Learning — Dive into Deep Learning 1.0.3 doc…](https://d2l.ai/) 

[Home on Ultralytics Platform](https://platform.ultralytics.com/home) 







## 版本迭代

| 版本 | 状态 | 记录 |
|---|---|---|
| 初始需求 | 已归档到 Git 历史 | 原始 MAIN 与本地资料边界 |
| v0.1.0 | 阶段 1 已确认，PR #1 已合并 | [首个模型、教程与真实基线实验](docs/05_experiments/v0.1.0_baseline.md) |
| v0.2.0 | PR #2 已按用户授权合并；阶段 2/3 待勾选 | [序列分组、三个开发候选与完整训练池 refit](docs/05_experiments/v0.2/README.md) |
| v0.3.0 | 阶段 4 桌面量化验证通过；PR #3 已合并 | [INT8 精度回归、图审计与 golden vectors](docs/05_experiments/v0.3/README.md) |

### 后续执行约定（用户补充）

- 交付时明确对应阶段编号；2026-10-04 用户确认阶段 1 并授权完成当前工作后合并。
- 在较短用量窗口或周额度的剩余额度接近 1% 时，先保存代码、实验产物和恢复说明，再停止；额度恢复后继续。
- 剩余额度通过应用的账号用量工具检查；不自动购买额度或消耗额外重置权益。

阶段 5 已收到 FPGA 工程，按用户要求从 GitHub 克隆到桌面 `CNN-Tutorial-FPGA`，禁止修改原 `fpga-w.-codex`。已完成工程核对和 RAW8 接口仿真，后续推进板端静态对齐、输入缩放和连续视频叠加；详见阶段 5 实施记录。




阶段 5.3：108 个翻译单元已编译、链接为 RISC-V ELF。教学入口：[05 静态固件](notebooks/05_riscv_static_bringup.ipynb)。未进行硬件下载，目标输出、arena 和 FPS 待测；原 FPGA 目录保持只读。
