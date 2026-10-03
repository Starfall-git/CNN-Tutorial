# 模型 1：GrayGestureCNN

## 任务边界

固定取景区域内出现一只手，输出 paper / rock / scissors 的分数。它解决整张图的分类，不能定位手的位置。第一版暂不处理空场景、多只手或其他手势；部署前必须加入真实无手背景/其他类，并单独验证拒识策略。

选择分类先于检测，是为了先闭合输入预处理、训练、模型导出、板端推理与显示的链路。检测还需要框标注、后处理和坐标映射，留给第二个模型。

## 输入与网络

输入 `N×1×64×64`，float32，范围 `[0,1]`。图像先转灰度，再用双线性缩放至 64×64，最后除以 255。官方样本是方形；真实 720p 摄像头应先裁取正方形 ROI，避免把整幅宽屏画面直接压成正方形。

| 层 | 输出（不含 batch） | 作用 |
|---|---|---|
| Conv 3×3, 1→8 + ReLU | 8×64×64 | 学习局部线条和边缘 |
| MaxPool 2×2 | 8×32×32 | 缩小空间尺寸 |
| Conv 3×3, 8→16 + ReLU | 16×32×32 | 组合局部手指形状 |
| MaxPool 2×2 | 16×16×16 | 降低后续计算量 |
| Conv 3×3, 16→32 + ReLU | 32×16×16 | 提取更复杂的局部结构 |
| MaxPool 2×2 + AvgPool 2×2 | 32×4×4 | 保留粗略空间分布 |
| Flatten + Linear | 3 | 输出未归一化的类别分数 |

三个卷积都使用 stride=1、padding=1 和 bias。网络没有 BatchNorm、Dropout 或自定义算子，便于后续逐层转换。选择 4×4 网格而非完全全局平均，是为了保留手指位置；代价是小规模全连接权重。

参数量由 `profile_model` 实测统计。卷积 MACs = 输出元素数 × 输入通道数 × 卷积核面积；线性层 MACs = 输入数 × 输出数。统计不包含池化比较、激活、访存或软件调度。

## 为什么输出 logits

`CrossEntropyLoss` 内部结合 log-softmax 和负对数似然。训练时再手动 softmax 会重复处理并降低数值稳定性。推理只需类别时，直接对 logits 使用 `argmax`；画概率图时才使用 softmax。softmax 高分不证明样本属于已知类别。

## 关键源码阅读

- `cnn_tutorial/model.py`：`nn.Sequential` 定义顺序网络，`forward` 定义数据流。
- `cnn_tutorial/data.py`：训练和推理共享灰度与归一化约定。
- `cnn_tutorial/training.py`：训练时计算梯度；验证时 `eval()` + `inference_mode()`。

章节组织借鉴 [D2L LeNet](https://d2l.ai/chapter_convolutional-neural-networks/lenet.html) 的“结构→张量形状→训练”顺序；这里的代码与文字针对本工程单独编写，不依赖 d2l 包。
