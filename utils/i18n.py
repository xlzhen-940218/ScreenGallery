import locale

def get_system_language():
    try:
        lang, _ = locale.getdefaultlocale()
        if lang and lang.startswith('zh'):
            return 'zh'
    except Exception:
        pass
    return 'en'

_CURRENT_LANG = get_system_language()

_TRANSLATIONS = {
    "zh": {
        "Smart Digital Photo Frame": "智能数码相框",
        "Today's Priority Tasks": "今日重要任务",
        "No photos selected or folder is empty.": "未选择照片或文件夹为空。",
        "Browse Folder": "浏览文件夹",
        "Select Photo Directory": "选择照片目录",
        "Score: ": "分数: ",
        "★ HIGH": "★ 高",
        "NORMAL": "普通",
        "HIGH": "高",
        "Enter new task...": "输入新任务...",
        "Add": "添加",
        "Close": "关闭",
        "Del": "删除",
        "CPU": "处理器",
        "RAM": "内存",
        "Mute": "静音",
        "Unmute": "取消静音"
    }
}

def tr(text):
    if _CURRENT_LANG == "zh" and text in _TRANSLATIONS["zh"]:
        return _TRANSLATIONS["zh"][text]
    return text
