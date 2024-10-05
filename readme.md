安装到Blender脚本库中
查看Python解析器路径（反馈结果在Window - Toggle System Console）中
```
import sys
print(sys.executable)
```
然后，在系统命令行中，输入
```
"D:\Program Files\blender-4.3.0\4.3\python\bin\python.exe" -m pip install openai
```

查看库的版本
```
import openai
print(openai.__version__)
```