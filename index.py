import json
import uvicorn
import urllib3
import requests
from typing import List
from random import choice
from loguru import logger
from fastapi import FastAPI
from jinja2 import Template
from fastapi.responses import RedirectResponse, HTMLResponse
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# 取消验证警报
urllib3.disable_warnings()

# 初始化变量
dataCache = []
allURLs = []
app = FastAPI()
scheduler = BackgroundScheduler()
cache_fileList_file = './cache/fileList.json'
cache_urlsList_file = './cache/urlsList.json'

noCacheHeaders = {
    'Authorization': 'Bearer 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',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
}

cdn = [
    'https://unifyz.s3.bitiful.net/mirrors/93hub/',
    'https://zeroctagon.s3.bitiful.net/mirrors/bangbang93HUB/',
]

# 文件列表相关函数
def read_fileList_from_cache():
    with open(cache_fileList_file, "r") as f:
        return json.loads(f.read())
    
def write_fileList_from_cache(data):
    with open(cache_fileList_file, "w") as f:
        json.dump(data, f)

# 地址列表相关函数
def read_urlsList_from_cache():
    with open(cache_urlsList_file, "r") as f:
        return json.loads(f.read())

def write_urlsList_from_cache(data):
    with open(cache_urlsList_file, "w") as f:
        json.dump(data, f)

# 填写
def fi_urlsList(name, path):
    return {
        'name': name, 
        'url': {
            'unifyz-bitiful': f'https://unifyz.s3.bitiful.net/mirrors/93hub/{path}',
            'zeroctagon-bitiful': f'https://zeroctagon.s3.bitiful.net/mirrors/bangbang93HUB/{path}'
        }
    }

def refresh_cache():
    global dataCache, allURLs
    dataCache.clear()
    allURLs.clear()
    root_folder_response = requests.get('https://api.github.com/repos/Mxmilu666/bangbang93HUB/contents', verify=False, headers=noCacheHeaders)
    if root_folder_response.status_code == 200:
        root_folder_json = root_folder_response.json()
        for root_folder_item in root_folder_json:
            if root_folder_item.get('type') == 'file' and 'readme' not in root_folder_item.get('name').lower():
                dataCache.append(root_folder_item.get('path'))
            if root_folder_item.get('type') == 'dir':
                sub_folder_response = requests.get(f'https://api.github.com/repos/Mxmilu666/bangbang93HUB/contents{root_folder_item.get("path")}', verify=False, headers=noCacheHeaders)
                if sub_folder_response.status_code == 200:
                    sub_folder_json = sub_folder_response.json()
                    for sub_folder_item in sub_folder_json:
                        if sub_folder_item.get('type') == 'file' and 'readme' not in sub_folder_item.get('name').lower():
                            dataCache.append(sub_folder_item.get('path'))
    write_fileList_from_cache(dataCache)
    logger.info("数据获取完成，已存储至 dataCache 列表中。")
    logger.info(f"当前拥有 {len(dataCache)} 个文件")
    allURLs = [fi_urlsList(i, i) for i in dataCache]
    write_urlsList_from_cache(allURLs)
    logger.info("全部文件数据，已存储至 allURLs 列表中。")


def save_file_in_s3(data: List[str], url: str):
    for i in data:
        requests.get(f"{url}{i}", headers=noCacheHeaders, verify=False)
    logger.info(f"在 {url}* 备份成功")
  
scheduler.add_job(refresh_cache, trigger=IntervalTrigger(hours=0.1))
scheduler.start()

# FastAPI 部分
@app.get("/")
def read_defaultPage():
    with open("index.html", "r", encoding='UTF8') as index_html_file:
        return HTMLResponse(content=index_html_file.read(), status_code=200)

@app.get("/bangbang93HUB/random")
def read_bangbang93HUB_random():
    return_url = f'{choice(cdn)}{choice(read_fileList_from_cache())}'
    return RedirectResponse(return_url, status_code=302)

@app.get("/bangbang93HUB/refreshCache")
def read_bangbang93HUB_refreshCache():
    refresh_cache()
    return {'message':'OK'}

@app.get("/bangbang93HUB/count")
def read_bangbang93HUB_count():
    return len(read_fileList_from_cache())

@app.get("/bangbang93HUB/all")
def read_bangbang93HUB_all():
    return read_urlsList_from_cache()

# 启动 uvicorn 服务器
if __name__ == '__main__':
    try:
        logger.info("服务启动中...")
        uvicorn.run(app, host='127.0.0.1', port=8000)
    except KeyboardInterrupt:
        logger.info("服务正在关闭中...")