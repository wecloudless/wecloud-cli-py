# ServerlessPilot

[TOC]

## ServerlessPilot 介绍

`ServerlessPilot`是基于服务器无感知计算的深度学习任务管理平台。它能够帮助开发者在各种实例上面部署深度学习任务，而开发者无需对下层的平台进行管理，`ServerlessPilot`使得开发者能够更加专注于深度学习任务的开发，减轻了开发者学习服务器管理的负担。

同时`ServerlessPilot`实现了对多种云服务的支持，并且向用户屏蔽了底层的细节。`ServerlessPilot`能够对深度学习任务进行自动解析，预估深度学习任务的时间，从而为用户提供多种部署方案，包括花费最少、运行最快等。

## 如何使用 ServerlessPilot

ServerlessPilot的使用主要包含两部分

- 使用命令行工具上传任务
- 在网页端部署任务
- 在网页端监控任务

### 使用命令行工具上传

#### 命令行工具的安装

命令行工具基于`python=3.10`运行，需要安装下列包

- python 3.10
- pip-packages
  - requests
  - click
  - pyyaml

#### 命令行工具的使用

- 命令行运行方式

  ```shell
  python main.py                              
  Usage: python main.py [OPTIONS] COMMAND [ARGS]...
  
  Options:
    --config TEXT  # 使用的部署文件
    --help         # 显示帮助
  
  Commands:
    deploy  # 将模型部署到 Serverless Pilot
    login   # 登录到 Serverless Pilot
  ```

- 部署

  ```shell
  python main.py deploy --path <workspace relative path> --job <job name>
  ```

  该命令将任务部署到`ServerlessPilot`，若用户未登录，则需要输入用户名和密码

  **⚠️注意⚠️**：用户需要在工作目录下面创建`.spilot.yaml`文件用于指定任务运行的环境和命令，该文件最少包含运行所需要的命令，默认环境配置命令为`pip install -r requirements.txt`，下面展示了`.spilot.yaml`的示例

  ```yaml
  run: 
    python -u train.py --net googlenet --gpu
  ```

  若工作目录下面不包含`.spilot.yaml`文件，则该命令会提示用户输入运行命令

- 登陆

  ```shell
  python main.py login
  ```

  该命令要求用户登陆`ServerlessPilot`，需要输入用户名和密码

#### 示例

- 假设任务代码文件定义在上层目录, 比如 `../image-classification/`.

- 假设`.spilot.yaml`文件定义如下 ，其中 `run` 是必须的，否则用户需要在命令行输入运行命令

  ```yaml
  run: 
    python -u train.py --net googlenet --gpu
  ```

- 运行部署命令之后，该命令会将任务打包上传到`ServerlessPilot`，`ServerlessPilot`会拉取镜像，创建容器，配置环境并运行任务。

- 在任务运行开始之后，命令行工具会启动浏览器，打开网页端控制台，之后用户可以在网页端查看任务解析过程并部署任务。

### 在网页端部署

在网页端部署任务主要包含两步，首先`ServerlessPilot`运行任务并自动解析，预估任务每轮的运行时间，然后给出推荐的部署方案。用户选择一个方案部署任务

#### 任务解析

命令行工具部署完毕之后会转到`ServerlessPilot`的训练任务的控制面板，该面板中用户可以查看任务的解析进度，点击`Select Task`然后选择任务即可，任务按照ID的字典序排列。

任务解析主要工作是预测当前任务在特定的配置下的运行时长。以深度学习训练为例，`ServerlessPilot`根据用户使用的数据集，预设的`batch_size`等参数，在不同的配置下运行训练任务，并以此预估训练任务每轮迭代花费的时间和成本。

<img src="assets/image-20230426181534100.png" alt="image-20230426181534100" style="zoom:20%;" />

<img src="assets/image-20230426181836958.png" alt="image-20230426181836958" style="zoom:20%;" />

#### 任务部署

任务解析完成之后，解析的结果会显示在当前页面。ServerlessPilot会自动估计每轮训练的时间并给出部署方案的建议，部署方案包含了任务部署的推荐配置以及预估的时间、预估的花费和推荐的提供商。配置方案包含多种，用户可以根据任务完成时间和花费进行选择，然后使用该方案部署即可。

<img src="assets/image-20230426182024988.png" alt="image-20230426182024988" style="zoom:20%;" />

### 在网页端监控

#### 在任务面板（Jobs panel）监控 

您可以通过侧边栏的`Jobs`进入任务面板，该面板会列出所有任务。您可以通过删除（`Delete`）删除任务

<img src="assets/image-20230426182604439.png" alt="image-20230426182604439" style="zoom:20%;" />

您可以通过点击任务名查看任务详情。任务的详情会显示在关于（`About`）界面.  任务详情包括任务部署的配置信息、任务的创建时间、任务运行时长等。您也可以在该页面删除任务

<img src="assets/image-20230426183045318.png" alt="image-20230426183045318" style="zoom:20%;" />

您也可以在日志（`log`）页面查看任务的输出

<img src="assets/image-20230426183220394.png" alt="image-20230426183220394" style="zoom:20%;" />

#### 在训练任务（Training jobs）面板监控

您可以通过下拉菜单进入训练任务（`Training jobs`）面板

<img src="assets/image-20230426183533407.png" alt="image-20230426183533407" style="zoom:20%;" />

您可以通过点击`info`获取任务的详情，之后会重定向到任务信息页面。

<img src="assets/image-20230426184011347.png" alt="image-20230426184011347" style="zoom:20%;" />

`ServerlessPilot`集成了`Tensorboard`. 你可以通过点击`Tensorboard`进入`Tensorboard`可视化页面

`VSCode` 和 `Jupyter Notebook` 正在研发中，敬请期待

#### 在总体（Overall）面板监控

该页面会显示资源的使用情况和任务列表。您也可以通过该页面获取任务的详情

<img src="assets/image-20230426184208766.png" alt="image-20230426184208766" style="zoom:20%;" />



## 示例

我们提供了一个端到端的示例，以展示`ServerlessPilot`的运行工作流程。您可以[点击这里](https://disk.pku.edu.cn:443/link/CC7619B71190026088E7B1D8FC206C55)查看示例。


