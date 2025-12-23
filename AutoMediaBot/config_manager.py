import os
import json
from datetime import datetime

# === 配置与文件路径 ===
CONFIG_FILE = "config.json"
LOG_LIMIT = 100

# 默认配置
default_config = {
    "llmApiKey": "", 
    "llmBaseUrl": "https://open.bigmodel.cn/api/paas/v4/", 
    "llmModel": "glm-4", 
    "wechatAppId": "",
    "wechatSecret": "",
    "topicLimit": 10,
    "scheduleCron": "0 */2 * * *", 
    "autoRun": False
}

# 全局运行时状态
runtime_state = {
    "isRunning": False,
    "lastRunTime": None,
    "nextRunTime": None,
    "logs": [],
    "hot_topics": [] 
}

# 全局配置对象
app_config = default_config.copy()

def load_config():
    """加载配置文件"""
    global app_config
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                app_config.update(saved)
            print("Config loaded successfully.")
        except Exception as e:
            print(f"Error loading config: {e}")

def save_config():
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(app_config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config: {e}")

def add_log(level: str, message: str):
    """全局日志记录函数"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        "id": int(datetime.now().timestamp() * 1000),
        "time": timestamp,
        "level": level,
        "message": message
    }
    # 保持日志长度
    runtime_state["logs"].insert(0, log_entry)
    if len(runtime_state["logs"]) > LOG_LIMIT:
        runtime_state["logs"].pop()
    
    # 控制台输出颜色区分 (简单处理)
    print(f"[{level.upper()}] {message}")

def get_config(key, default=None):
    return app_config.get(key, default)

def update_app_config(new_config: dict):
    app_config.update(new_config)
    save_config()