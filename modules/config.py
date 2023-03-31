from contextlib import contextmanager
import os
import logging
import sys
import json

__all__ = [
    "my_api_key",
    "authflag",
    "auth_list",
    "dockerflag",
    "retrieve_proxy",
    "log_level",
]

# 添加一个统一的config文件，避免文件过多造成的疑惑（优先级最低）
# 同时，也可以为后续支持自定义功能提供config的帮助
if os.path.exists("config.json"):
    with open("config.json", "r", encoding='utf-8') as f:
        config = json.load(f)
else:
    config = {}

## 处理docker if we are running in Docker
dockerflag = config.get("dockerflag", False)
if os.environ.get("dockerrun") == "yes":
    dockerflag = True

## 处理 api-key 以及 允许的用户列表
my_api_key = config.get("openai_api_key", "") # 在这里输入你的 API 密钥
authflag = "users" in config
auth_list = config.get("users", []) # 实际上是使用者的列表
my_api_key = os.environ.get("my_api_key", my_api_key)
if dockerflag:
    if my_api_key == "empty":
        logging.error("Please give a api key!")
        sys.exit(1)
    # auth
    username = os.environ.get("USERNAME")
    password = os.environ.get("PASSWORD")
    if not (isinstance(username, type(None)) or isinstance(password, type(None))):
        auth_list.append((os.environ.get("USERNAME"), os.environ.get("PASSWORD")))
        authflag = True
else:
    if (
        not my_api_key
        and os.path.exists("api_key.txt")
        and os.path.getsize("api_key.txt")
    ):
        with open("api_key.txt", "r") as f:
            my_api_key = f.read().strip()
    if os.path.exists("auth.json"):
        authflag = True
        with open("auth.json", "r", encoding='utf-8') as f:
            auth = json.load(f)
            for _ in auth:
                if auth[_]["username"] and auth[_]["password"]:
                    auth_list.append((auth[_]["username"], auth[_]["password"]))
                else:
                    logging.error("请检查auth.json文件中的用户名和密码！")
                    sys.exit(1)

@contextmanager
def retrieve_openai_api(api_key = None):
    old_api_key = os.environ.get("OPENAI_API_KEY", "")
    if api_key is None:
        os.environ["OPENAI_API_KEY"] = my_api_key
        yield my_api_key
    else:
        os.environ["OPENAI_API_KEY"] = api_key
        yield api_key
    os.environ["OPENAI_API_KEY"] = old_api_key

## 处理log
log_level = config.get("log_level", "INFO")
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
)

## 处理代理：
http_proxy = config.get("http_proxy", "")
https_proxy = config.get("https_proxy", "")
http_proxy = os.environ.get("HTTP_PROXY", http_proxy)
https_proxy = os.environ.get("HTTPS_PROXY", https_proxy)

# 重置系统变量，在不需要设置的时候不设置环境变量，以免引起全局代理报错
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""

@contextmanager
def retrieve_proxy(proxy=None):
    """
    1, 如果proxy = NONE，设置环境变量，并返回最新设置的代理
    2，如果proxy ！= NONE，更新当前的代理配置，但是不更新环境变量
    """
    global http_proxy, https_proxy
    if proxy is not None:
        http_proxy = proxy
        https_proxy = proxy
        yield http_proxy, https_proxy
    else:
        old_var = os.environ["HTTP_PROXY"], os.environ["HTTPS_PROXY"]
        os.environ["HTTP_PROXY"] = http_proxy
        os.environ["HTTPS_PROXY"] = https_proxy
        yield http_proxy, https_proxy # return new proxy
        
        # return old proxy
        os.environ["HTTP_PROXY"], os.environ["HTTPS_PROXY"] = old_var


## 处理advance pdf
advance_pdf = config.get("advance_pdf", {})