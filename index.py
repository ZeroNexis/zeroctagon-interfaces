import json
import uvicorn
import urllib3
import requests
from typing import List
from random import choice
from loguru import logger
from jinja2 import Template
from fastapi import FastAPI, Response, status
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
bangbang93HUB_cache_fileList_file = './cache/bangbang93HUB/fileList.json'
bangbang93HUB_cache_urlsList_file = './cache/bangbang93HUB/urlsList.json'

noCacheHeaders = {
    'Authorization': 'Bearer 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',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
}

cdn = [
    'https://unifyz.s3.bitiful.net/mirrors/93hub/',
    'https://zeroctagon.s3.bitiful.net/mirrors/bangbang93HUB/'
]

# 文件列表相关函数
def read_fileList_from_cache():
    with open(bangbang93HUB_cache_fileList_file, "r") as f:
        return json.loads(f.read())
    
def write_fileList_from_cache(data):
    with open(bangbang93HUB_cache_fileList_file, "w") as f:
        json.dump(data, f)

# 地址列表相关函数
def read_urlsList_from_cache():
    with open(bangbang93HUB_cache_urlsList_file, "r") as f:
        return json.loads(f.read())

def write_urlsList_from_cache(data):
    with open(bangbang93HUB_cache_urlsList_file, "w") as f:
        json.dump(data, f)

# 填写
def fi_urlsList(name, path):
    return {
        'name': name, 
        'urls': {
            'uni-bitiful': f'https://unifyz.s3.bitiful.net/mirrors/93hub/{path}',
            'zero-bitiful': f'https://zeroctagon.s3.bitiful.net/mirrors/bangbang93HUB/{path}'
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
            if root_folder_item.get('type') == 'dir' and '.github' not in root_folder_item.get('name').lower():
                sub_folder_response = requests.get(f'https://api.github.com/repos/Mxmilu666/bangbang93HUB/contents{root_folder_item.get("path")}', verify=False, headers=noCacheHeaders)
                if sub_folder_response.status_code == 200:
                    sub_folder_json = sub_folder_response.json()
                    for sub_folder_item in sub_folder_json:
                        if sub_folder_item.get('type') == 'file' and 'readme' not in sub_folder_item.get('name').lower():
                            dataCache.append(sub_folder_item.get('path'))
    write_fileList_from_cache(dataCache)
    logger.info(f"当前拥有 {len(dataCache)} 个文件")
    logger.info("数据获取完成，已存储至 dataCache 列表中。")
    allURLs = [fi_urlsList(i, i) for i in dataCache]
    write_urlsList_from_cache(allURLs)
    logger.info("全部文件数据，已存储至 allURLs 列表中。")


def save_file_in_s3(data: List[str], url: str):
    for i in data:
        requests.get(f"{url}{i}", headers=noCacheHeaders, verify=False)
    logger.info(f"在 {url}* 备份成功")
  
# scheduler.add_job(refresh_cache, trigger=IntervalTrigger(hours=0.1))
# scheduler.start()

# FastAPI 部分
@app.get("/")
def read_defaultPage():
    return RedirectResponse('https://apifox.com/apidoc/shared-8f05dbb5-68f5-4fd4-b178-00568b210e00', status_code=302)

# bangbang93HUB 部分
@app.get("/bangbang93HUB/random")
def read_bangbang93HUB_random(response: Response, type: str | None = 'image'):
    return_name = f'{choice(read_fileList_from_cache())}'
    if type == 'image':
        return RedirectResponse(f'{choice(cdn)}{return_name}', status_code=302)
    elif type == 'json':
        response.status_code = status.HTTP_200_OK
        return {
            "code": 200,
            "message": "OK",
            "data": {
                "url": f'{choice(cdn)}{return_name}',
                "name": f'{return_name}',
            }
        }
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "code": 400,
            "message": "Bad Request"
        }

@app.get("/bangbang93HUB/refreshCache")
def read_bangbang93HUB_refreshCache(response: Response):
    refresh_cache()
    response.status_code = status.HTTP_200_OK
    return {
        "code": 200,
        "message": "OK"
    }

@app.get("/bangbang93HUB/count")
def read_bangbang93HUB_count(response: Response, type: str | None = 'text'):
    if type == 'text':
        response.status_code = status.HTTP_200_OK
        return len(read_fileList_from_cache())
    elif type == 'json':
        response.status_code = status.HTTP_200_OK
        return {
            "code": 200,
            "message": "OK",
            "data": {
                "count": len(read_fileList_from_cache())
            }
        }
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "code": 400,
            "message": "Bad Request"
        }

@app.get("/bangbang93HUB/all")
def read_bangbang93HUB_all():
    return read_urlsList_from_cache()

@app.get("/bangbang93HUB/saveInS3")
def read_bangbang93HUB_saveInS3(response: Response):
    save_file_in_s3(read_fileList_from_cache(), 'https://zeroctagon.s3.bitiful.net/mirrors/bangbang93HUB/')
    response.status_code = status.HTTP_200_OK
    return {
        "code": 200,
        "message": "OK"
    }

# 启动 uvicorn 服务器
if __name__ == '__main__':
    try:
        logger.info("服务启动中...")
        uvicorn.run(app, host='127.0.0.1', port=8000)
    except KeyboardInterrupt:
        logger.info("服务正在关闭中...")