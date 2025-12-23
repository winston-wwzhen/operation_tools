AutoMediaBot 启动指南
1. 环境准备
请确保你的电脑上已经安装了 Python 3.8 或更高版本。
2. 快速启动 (推荐)
Windows 用户: 直接双击运行 start.bat。
Mac/Linux 用户: 在终端运行 sh start.sh。
这些脚本会自动完成以下步骤：
创建虚拟环境 (venv)
激活环境
安装依赖 (pip install)
安装浏览器驱动 (playwright install)
启动服务
3. 手动启动步骤
如果你想手动一步步操作，请参考以下命令：
第一步：创建虚拟环境
# Windows
python -m venv venv

# Mac/Linux
python3 -m venv venv


第二步：激活虚拟环境
# Windows
.\venv\Scripts\activate

# Mac/Linux
source venv/bin/activate


激活成功后，命令行前面会出现 (venv) 字样。
第三步：安装依赖
pip install -r requirements.txt
playwright install chromium


第四步：启动服务
# 方式一：直接运行 python 文件
python server.py

# 方式二：使用 uvicorn (支持热重载，开发推荐)
uvicorn server:app --host 0.0.0.0 --port 3000 --reload


4. 访问控制台
服务启动后，打开浏览器访问：http://localhost:3000
