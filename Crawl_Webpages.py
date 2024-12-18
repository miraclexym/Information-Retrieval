# 验证 Elasticsearch 服务已启动

from elasticsearch import Elasticsearch

# 添加 'scheme' 参数，指定连接协议
es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])

# 检查 Elasticsearch 服务是否运行
if not es.ping():
    print("Elasticsearch 服务未响应!")
else:
    print("Elasticsearch 服务已启动!")

# 网页爬取
import requests
from bs4 import BeautifulSoup
import time
import random
import re
import os
import pickle
import csv
from urllib.parse import urljoin
import hashlib  # 用于计算 URL 的哈希值
import chardet  # 用于自动检测网页编码

# 设置爬虫基本参数
BASE_URL = "http://www.nankai.edu.cn/"  # 南开大学官网
MAX_PAGES = 100000
DELAY = 0.001
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
HEADERS = {"User-Agent": USER_AGENT}

# 设置文件存储路径
SAVE_DIR = "HtmlFile"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# 存储爬虫状态的文件路径
STATE_FILE = "crawling_state.pkl"
# 存储网页内容的 CSV 文件路径
CSV_FILE = "Html_File.csv"

def fetch_page(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            # 检测页面的编码
            encoding = response.apparent_encoding  # apparent_encoding会自动推断编码
            response.encoding = encoding  # 根据推断的编码设置正确的编码
            return response.text
        else:
            print(f"Failed to retrieve {url} with status code {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_page(url, html):
    soup = BeautifulSoup(html, "html.parser")
    
    # 提取网页标题
    title = soup.title.string if soup.title else "No Title"
    if not title:  # 如果没有标题，尝试从 meta 标签中获取
        meta_title = soup.find("meta", {"name": "description"})
        if meta_title:
            title = meta_title.get("content", "No Title")
        else:
            title = "No Title"
    
    # 清理标题，避免包含非法字符
    title = clean_filename(title)

    # 保存网页内容到本地文件
    save_page_to_file(url, html, title)

    return {
        "url": url,
        "title": title,
        "timestamp": time.time(),
    }

# 保留的 Windows 文件名
RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL", 
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}

def clean_filename(filename):
    # 如果 filename 是 None 或空字符串，返回一个默认名称
    if not filename:
        return "untitled_page"

    # 限制文件名长度为 100 个字符
    if len(filename) > 100:
        filename = filename[:100]

    # 去除开头和结尾的空格
    filename = filename.strip()

    # 如果 filename 不是 None 类型，则执行编码和清理操作
    filename = filename.replace("\r", "").replace("\t", "").replace("\n", "")  # 去掉换行符
    filename = re.sub(r'[\\/:*?"<>|]', '', filename)  # 替换非法字符

    # 检查文件名是否为保留的名称
    if filename.upper() in RESERVED_NAMES:
        filename = filename + "_page"
        
    # 去除文件名末尾的点和空格
    filename = filename.rstrip(" .")

    return filename

def save_page_to_file(url, html, title):

    # 创建文件路径
    file_name = f"{title}.html"
    file_path = os.path.join(SAVE_DIR, file_name)

    # 如果文件已经存在，添加时间戳后缀
    if os.path.exists(file_path):
        timestamp = int(time.time())  # 获取当前时间戳
        file_name = f"{title}_{timestamp}.html"
        file_path = os.path.join(SAVE_DIR, file_name)

    # 保存网页 HTML 内容到文件
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(html)
    print(f"Page saved to {file_path}")
    return True  # 返回 True，表示文件已成功保存

def extract_links(url, html):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    
    # 提取所有的 <a> 标签，并获取其中的 href 属性
    for a_tag in soup.find_all("a", href=True):
        link = a_tag["href"]
        
        # 处理相对链接和绝对链接
        if link.startswith("http"):
            links.add(link)
        else:
            # 使用 urljoin 处理相对链接
            full_link = urljoin(url, link)
            
            # 过滤掉一些不需要的链接，如锚点（#）或空链接
            if not full_link.endswith("#") and full_link != url:
                links.add(full_link)
        
    return links

def save_state(to_crawl, crawled):
    # 保存当前的抓取状态到文件
    with open(STATE_FILE, 'wb') as state_file:
        pickle.dump((to_crawl, crawled), state_file)
    print(f"State saved to {STATE_FILE}")

def load_state():
    # 从文件加载之前保存的爬虫状态
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'rb') as state_file:
            to_crawl, crawled = pickle.load(state_file)
        print(f"State loaded from {STATE_FILE}")
        return to_crawl, crawled
    else:
        return set(), set()

def save_to_csv(data):
    # 保存网页信息到 CSV 文件
    file_exists = os.path.exists(CSV_FILE)
    
    with open(CSV_FILE, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            # 写入标题行
            writer.writerow(["title", "url"])
        writer.writerow([data["title"], data["url"]])
    print(f"Page data saved to {CSV_FILE}")

def get_url_hash(url):
    # 确保 url 是字符串类型
    url = str(url)
    # 使用 hashlib 计算 URL 的哈希值
    return hashlib.md5(url.encode('utf-8')).hexdigest()

def crawl(start_url):
    # 尝试从文件加载之前的状态
    to_crawl, crawled = load_state()
    
    # 如果起始 URL 不在待抓取列表中，加入待抓取列表
    to_crawl.add(start_url)

    while to_crawl and len(crawled) < MAX_PAGES:
        url = to_crawl.pop()
        
        # 获取 URL 的哈希值
        url_hash = get_url_hash(url)

        # 如果该 URL 的哈希值已存在于 crawled 集合中，跳过
        if url_hash in crawled:
            continue

        # 如果 URL 后缀是 .mp4，则跳过这个 URL
        if url.endswith('.mp4'):
            print(f"Skipping: {url} (MP4 file)")
            continue

        # 如果 URL 后缀是 .png，则跳过这个 URL
        if url.endswith('.png'):
            print(f"Skipping: {url} (PNG file)")
            continue

        # 如果 URL 后缀是 .jpg，则跳过这个 URL
        if url.endswith('.jpg'):
            print(f"Skipping: {url} (JPG file)")
            continue

        # 如果 URL 后缀是 .pdf，则跳过这个 URL
        if url.endswith('.pdf'):
            print(f"Skipping: {url} (PDF file)")
            continue

        print(f"Crawling: {url}")
        html = fetch_page(url)
        
        if html:
            document = parse_page(url, html)
            
            # 保存页面数据到 CSV 文件
            save_to_csv(document)
            # 文件成功保存，则更新状态
            crawled.add(url_hash)  # 使用 URL 的哈希值进行存储
            # 提取新的链接
            new_links = extract_links(url, html)
            # 更新待爬取链接集合
            to_crawl.update(new_links)

        # 每次抓取后保存状态
        save_state(to_crawl, crawled)
        
        # 随机延迟
        time.sleep(DELAY + random.uniform(0.000, 0.009))

if __name__ == "__main__":
    crawl(BASE_URL)  # 从 BASE_URL 开始抓取