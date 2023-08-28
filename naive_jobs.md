# ServerlessPilot

[TOC]

## ServerlessPilot 介绍

`ServerlessPilot`是基于服务器无感知计算的深度学习任务管理平台。它能够帮助开发者在各种实例上面部署深度学习任务，而开发者无需对下层的平台进行管理，`ServerlessPilot`使得开发者能够更加专注于深度学习任务的开发，减轻了开发者学习服务器管理的负担。

`ServerlessPilot`实现了对多种云服务的支持，并且向用户屏蔽了底层的细节。同时，`ServerlessPilot`能够对深度学习任务进行自动解析，预估深度学习任务的时间，从而为用户提供多种部署方案，包括花费最少的方案、运行最快的方案等。

## 如何使用 ServerlessPilot

ServerlessPilot目前支持`Naive Job`和`ElasticFlow Job`两类作业。其中，`Naive Job`无需对任务本身进行修改，本文档主要介绍如何部署`Naive Job`。

ServerlessPilot的使用主要包含四部分：
- 任务代码开发
- 使用命令行工具上传任务
- 在网页端部署任务
- 在网页端监控任务

### 1. Naive Job代码开发

#### 1.1 代码开发
用户可自由开发代码，仅需在任务目录`<your_job>`下额外添加`.spilot.yaml`文件，该文件中应该至少包含`image`镜像和`run`任务执行指令，可选加入`setup`环境配置指令和`profile`任务刻画指令。请参考[示例](https://github.com/wecloudless/wecloud_example)。

  **⚠️注意⚠️**：为保障任务上传效率，任务代码大小限制为100MB，请将数据集、模型参数等较大的文件上传到在线平台（如Google Drive等），并在任务里添加获取在线文件的代码。

  **⚠️注意⚠️**：请在代码中使用相对路径访问和保存子模块、数据集和模型参数等。

#### 1.2 镜像
任务使用的镜像需在`.spilot.yaml`文件中通过`image`指定，现支持如下两类镜像：
- 使用本平台提供的默认镜像`wangqipeng/wecloud_train:v0.2.0`，该镜像包括以下库：
  ```
  python=3.7
  pytorch=1.9
  ```
  如需其他依赖库，请将依赖写入`<your_job>/requirements.txt`。[示例](https://github.com/wecloudless/wecloud_example)中即使用该种镜像。

- 使用Docker Hub上已有的docker image。用户可以使用Docker Hub上已有的docker image；或将自定义的docker image打包上传至Docker Hub，然后编辑`.spilot.yaml`文件中的`image`，指定自定义的docker image:
  ```
  # .spilot.yaml
  image: <user>/<repo>:<tag>
  ```

### 2. 使用命令行工具上传

#### 2.1 命令行工具的安装

命令行工具基于`python=3.10`运行，安装指令如下：
```shell
# 安装好python 3.10后
pip install pipenv
pipenv shell
```

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

命令行工具的常用指令包括登陆和上传任务：
- 登陆

  ```shell
  python main.py login
  ```

  该命令要求用户登陆`ServerlessPilot`，需要输入用户名和密码

- 上传任务

  ```shell
  python main.py deploy --path <your_job> --job <job name>
  ```

  该命令将任务上传到`ServerlessPilot`，若用户未登录，则需要输入用户名和密码

  **⚠️注意⚠️**：job name中不能带有下划线“_”，否则后续k8s会报错！


### 3. 在网页端部署

命令行工具将任务上传完毕后，会在浏览器中自动打开`ServerlessPilot`的任务控制面板，显示刚上传的任务和多个推荐部署方案。选择一个部署方案并点击`Deploy`按钮即可部署。
<img src="assets/image-20230816.png" alt="image-20230816" style="zoom:20%;" />

如需选择其他任务，可以在任务面板中点击`Select Task`并选择其他任务。
<img src="assets/select_task.png" alt="image-20230426181534100" style="zoom:20%;" />

<img src="assets/select_task2.png" alt="image-20230426181836958" style="zoom:20%;" />


### 4. 在网页端监控

#### 4.1 在任务面板（Jobs panel）监控 

您可以通过侧边栏的`Jobs`进入任务面板，该面板会列出所有任务。您可以通过删除（`Delete`）删除任务。

<img src="assets/jobs.png" alt="image-20230426182604439" style="zoom:20%;" />

您可以通过点击任务名查看任务详情。任务的详情会显示在关于（`About`）界面.  任务详情包括任务部署的配置信息、任务的创建时间、任务运行时长等。您也可以在该页面删除任务。

<img src="assets/jobs_about.png" alt="image-20230426183045318" style="zoom:20%;" />

您也可以在日志（`Log`）页面查看任务的输出。

<img src="assets/jobs_log.png" alt="image-20230426183220394" style="zoom:20%;" />

#### 4.2 下载任务输出

在上传任务代码时，请将所有需要输出的文件（例如训练得到的模型检查点）输出到目录`<your_job>/output`内。
**代码中必须使用相对路径`./output`， 不能使用绝对路径**。


## 示例

我们提供了使用`ServerlessPilot`平台的完整演示视频，以展示本平台的工作流程。您可以[点击这里](https://disk.pku.edu.cn:443/link/CC7619B71190026088E7B1D8FC206C55)查看示例。

## 问题反馈
如果在使用CLI的时候遇到问题，请按照[该样例](https://github.com/wecloudless/wecloud-cli-py/issues/1)提交issue进行反馈。
