# 版本迭代说明与约束申明

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

- [ ] 1. 先分步尝试搭建第一个模型（选择更简单的那一个，物品识别/手势识别），搭建时参考d2l.ai教程的风格来解释，但是不要解释的过多过详细也不要太浅显。

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





