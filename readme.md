# Blender插件 唇形同步&3D虚拟人 直播数字人Lip sync & 3D digital human
## 第一部分 软件简介

### 一、Lip Sync是什么？
Lip sync & 3D digital human是一款Blender专用的插件，通过3D对象，实现实时唇形同步，与动画操作，达到虚拟数字人的效果。
### 二、Lip Sync特点
目前，市场上有许多的3D虚拟人，为什么还要开发这样一个插件？
Blender4.2实时渲染器EEVEE的更新，为Lip sync & 3D digital human的实现提供了可能，同Unity、UE一样，实现实时渲染。
免费开源
	Blender的开源性
	插件代码的开源性
形象定制
	3D形象角色的定制性
	内容生成的定制性
全程介入
	从语音转文本，文本内容生成，文本转语音，唇形同步动画……每一步，都可以介入；而且，可跳过执行过程，直接通过语音、文字实现动画生成。
### 三、Lip Sync的原理/ 流程

![[Lip Sync.svg]]
在此，非常感谢大佬@阴沉的怪咖，生成原理基本参考了他的[[chatgpt+unity]二次元AI女友合集](https://www.bilibili.com/video/BV1CT411X7Dm/ "[chatgpt+unity]二次元AI女友合集")。

## 第二部分 软件安装
### 一、插件下载
[dukeren/lip_sync_3D_digital_human: lip_sync_3D_digital_human (github.com)](https://github.com/dukeren/lip_sync_3D_digital_human)
### 二、外部依赖库安装

` Lip sync & 3D digital human`需要2个Python外部依赖库
	openai（Api调用）
	librosa（音素提取）
#### 1、Windows命令行安装
打开Python控制台（反馈结果在Window - Toggle System Console）中
```
import sys
print(sys.executable)
```
安装openai依赖库（注意：Windows CMD下）
```
"D:\Program Files\blender-4.3.0-alpha+main.1ede471ba2b5-windows.amd64-release\4.3\python\bin\python.exe" -m pip install openai
```
安装librosa依赖库
```
"D:\Program Files\blender-4.3.0-alpha+main.1ede471ba2b5-windows.amd64-release\4.3\python\bin\python.exe" -m pip install librosa
```
查看库的版本
openai
```
import openai
print(openai.__version__)
```
librosa
```
import librosa
print(librosa.__version__)
```
#### 2、Python控制器安装
openai
```
import subprocess
import sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "openai"])
```
librosa
```
import subprocess
import sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "librosa"])
```
### 三、插件安装
#### 1、常规安装
打开Blender，进入`Edit` -> `Preferences`。
选择`Add-ons`选项卡。
点击`Install`按钮，选择插件的`.zip`文件。
安装后，勾选插件以启用它。
#### 2、手工安装
复制文件夹到Blender插件目录。
插件目录一般为Blender安装目录下的`Blender版本\scripts、addon`文件夹之中。
打开Blender，进入`Edit` -> `Preferences`。
选择`Add-ons`选项卡，`刷新本地`，搜索并勾选` Lip sync & 3D digital human`
#### 四、外部大模型安装
` Lip sync & 3D digital human`的正常运行，需要至少3个大语言模型的支持：
	语音转文本模型（whisper-asr-webservice）
	文本/内容生成模型（OpenAI、Ollama、Dify……）
	文本转语音模型（ChatTTS-ui）
#### 1、whisper-asr-webservice
安装Docker Desktop
[Get Started | Docker](https://www.docker.com/get-started/)
加入系统变量
接取镜像
```
docker run -e ASR_MODEL=medium -p 9000:9000 --gpus all --name whisper_asr_webservice onerahmet/openai-whisper-asr-webservice:latest-gpu
```
其中，`ASR_MODEL=medium`可以设置语音模型，'tiny.en', 'tiny', 'base.en', 'base', 'small.en', 'small', 'medium.en', 'medium', 'large-v1', 'large-v2', 'large-v3', 'large'等
注：更改端口就访问不了
#### 2、Ollama安装
##### A、下载地址
[Download Ollama on Windows](https://ollama.com/download)
##### B、设置环境变量（默认模型目录）
我的电脑-右键-系统-高级系统设置-高级-环境变量-系统变量
新建系统变量
```
OLLAMA_MODELS
```
输入路径即可
##### C、模型拉取
```
ollama run llama3.1
```
##### D、运行服务
```
ollama serve
```
#### 3、ChatTTS-ui安装
[jianchang512/ChatTTS-ui: 一个简单的本地网页界面，使用ChatTTS将文字合成为语音，同时支持对外提供API接口。 ](https://github.com/jianchang512/ChatTTS-ui?tab=readme-ov-file)
##### A、安装虚拟环境
```
conda create -n chattts python=3.11
```
##### B、Git库
```
git clone https://github.com/jianchang512/ChatTTS-ui.git
```
##### C、配置ffmpeg
进入官网[FFmpeg](https://ffmpeg.org/),选择Download-window，以第一个为例，进入，选择左栏[release builds](https://www.gyan.dev/ffmpeg/builds/#release-builds)，你可以选择下载上面 release-full 版本，或者选择下面稳定版本 xxx-full_build，release-full 版本会比下面的 xxx-full_build 版本更新，选择哪一个都可以，看你个人喜好。
下载 ffmpeg.exe 放在 软件目录下的ffmpeg文件夹内
##### D、在目录下激活虚拟环境
```
conda activate chattts
```
##### D、安装依赖
```
pip install -r requirements.txt
```
注：官方可能还缺少一个库，安装即可
```
pip install pandas
```
##### E、安装cu118
```
pip install torch==2.2.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cu118
```
注：首先系统安装CUDA11.8+ ToolKit，[CUDA Toolkit Archive | NVIDIA Developer](https://developer.nvidia.com/cuda-toolkit-archive)，默认安装

##### 运行
```
python app.py
```
启动，将自动打开浏览器窗口，默认地址 `http://127.0.0.1:9966` (注意：默认从 modelscope 魔塔下载模型，不可使用代理下载，请关闭代理)
注：第一次将从huggingface.co或github下载模型到asset目录下，如果网络不稳，可能下载失败，若是失败，请单独下载
下载后解压后，会看到asset文件夹，该文件夹内有多个pt文件，将所有pt文件复制到asset目录下，然后重启软件
GitHub下载地址: [https://github.com/jianchang512/ChatTTS-ui/releases/download/v1.0/all-models.7z](https://github.com/jianchang512/ChatTTS-ui/releases/download/v1.0/all-models.7z)
百度网盘下载地址: [https://pan.baidu.com/s/1yGDZM9YNN7kW9e7SFo8lLw?pwd=ct5x](https://pan.baidu.com/s/1yGDZM9YNN7kW9e7SFo8lLw?pwd=ct5x)
generated_content
#### 五、3D模型准备
至少有A、I、U、O、E五个基础口型形态键。
模型来源
#### Blender插件

## 第三部分 基础使用
### 一、外部大模型启用
	运行whisper-asr-webservice）
	运行Ollama（Dify、OpenAI……）
	运行ChatTTS-ui
### 二、界面及功能简介
三个选项页：内容生成、动画生成、视频同步
#### 1、内容生成
1. 输入类型 (Input Method)
    - 这是一个下拉菜单，允许用户选择输入方式。
    - 有两个选项：  
        a. "Listen on Port"：监听特定端口以接收输入。
        - 如果选择此选项，会显示以下额外选项：
            - 监听端口 (Listening Port)：用户可以设置要监听的端口号（默认为9990）。
            - 开始/停止监听按钮：根据当前状态，显示"开始监听"或"停止监听"。  
                b. "Select File"：选择并处理文本文件。
        - 如果选择此选项，会显示"Select and Process Text File"按钮。
2. 语音转文本 (Speech to Text)
    - 这是一个下拉菜单，用于选择语音转文本的方法。
    - 选项包括：  
        a. Whisper  
        b. Other Voice Assistant
3. 文本生成 (Content Generation)
    - 这是一个下拉菜单，用于选择内容生成的方法。
    - 选项包括：  
        a. OpenAI  
        b. Ollama  
        c. Dify
4. 文本转语音 (Text to Speech)
    - 这是一个下拉菜单，用于选择文本转语音的方法。
    - 选项包括：  
        a. ChatTTS  
        b. Other

这些选项允许用户灵活地配置内容生成过程的各个阶段，包括输入方式、语音识别、内容生成和语音合成。用户可以根据自己的需求和偏好选择不同的方法和设置。
#### 2、动画生成
动画生成，包含三个主要的内容：音频文件检测、唇型动画设置、闲置动画设置
- 音频文件检测：
	- 实时检测：实时动画
	- 语音文件选择：根据语音文件生成特定动画
- 唇型动画设置：
    - "唇型对象"：选择要应用唇型动画的3D模型对象。
    - "帧率"：设置动画的帧率，通常保持与场景帧率一致。
    - "静音阈值"：设置识别静音的音量阈值。
    - "最大静音帧数"：设置连续静音的最大帧数。
    - "语言"：选择音频的语言（中文或英文），以使用相应的音素到口型映射。
- 闲置动画设置：
    - "自定义帧数"：设置闲置动画的总帧数，0表示使用场景的结束帧。
    - 闲置动画列表：显示已添加的闲置动画，每个动画包含以下设置：
        - 名称
        - 对象：选择应用闲置动画的3D模型对象。
        - 形态键：选择用于闲置动画的形态键。
        - 最小/最大间隔：设置闲置动画触发的时间间隔范围。
        - 最小/最大持续时间：设置闲置动画的持续时间范围。
    - "添加闲置动画" 按钮：添加新的闲置动画设置。
    - "生成闲置动画" 按钮：根据设置生成闲置动画。
    - "清除闲置动画" 按钮：清除所有对象的闲置动画。
#### 3、视频同步
提供了一些控制视频播放和音频同步的功能。
1. 打开/关闭播放器面板
    - 点击 "打开播放器面板" 或 "关闭播放器面板" 按钮来展开或折叠播放器控制选项。（因为里面有播放/循环控制功能，为不影响Blender正常使用，被迫做了激活面板设置）
2. 选择背景音乐
    - 点击 "选择背景音乐" 按钮来打开文件浏览器。
    - 选择一个音频文件作为自定义背景音乐。
3. 播放控制
    - 开始播放：当视频未在播放时，点击 "开始播放" 按钮来开始播放视频和音频。
    - 暂停播放：当视频正在播放时，点击 "暂停播放" 按钮来暂停当前播放。
    - 停止播放：当视频正在播放时，点击 "停止播放" 按钮来停止播放并重置到开始位置。
4. 循环播放
    - 勾选 "循环播放" 复选框，使视频和音频在播放结束后自动重新开始。
5. 背景音乐音量
    - 使用滑块调节背景音乐的音量，范围从0（静音）到1（最大音量）。
6. LipSync对象
    - 从下拉菜单中选择要应用唇形同步的3D模型对象。这个对象应该包含用于唇形同步的形态键。