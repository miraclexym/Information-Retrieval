import os
import csv
import re
from bs4 import BeautifulSoup

# 假设html文件夹路径
html_folder_path = './HtmlFile'

# 读取HtmlFile.csv并获取html文件名称和URL
def read_csv(csv_file):
    with open(csv_file, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # 跳过表头
        file_data = [row for row in reader]
    return file_data

# 提取html文件中的信息：标题、URL、锚文本、正文
def extract_html_info(html_file, url, html_file_name):
    with open(html_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

        # 直接使用文件名作为标题
        title = html_file_name  # 这里将title设置为文件名

        # 提取正文，通常为 <body> 标签中的内容
        body = soup.find('body')
        body_text = body.get_text(strip=True) if body else '无正文'

        # 格式化正文，去除换行符、制表符等
        formatted_body = format_text(body_text)

        # 提取锚文本（<a>标签的文本）
        anchors = soup.find_all('a')
        anchor_texts = [a.get_text(strip=True) for a in anchors]

        # 返回提取的信息
        return {
            'title': title,
            'url': url,
            'anchors': anchor_texts,
            'body': formatted_body
        }

# 格式化文本：去除多余的空格、换行符、制表符等
def format_text(text):
    # 使用正则表达式去除多余的空白字符（换行、制表符、多个空格等）
    text = re.sub(r'\s+', ' ', text)  # 替换所有类型的空白字符（如换行、空格等）为单个空格
    text = text.strip()  # 去掉文本开头和结尾的空白字符
    return text

# 构建索引并写入到新的CSV文件
def build_index_and_write_to_csv(file_data, output_csv_file):
    # 创建并打开CSV文件进行写入
    with open(output_csv_file, mode='w', encoding='utf-8', newline='') as csvfile:
        fieldnames = ['title', 'url', 'anchors', 'body']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()  # 写入表头

        # 遍历每一行文件数据，提取HTML信息并写入CSV文件
        for row in file_data:
            html_file_name = row[0]  # 获取html文件名
            url = row[1]  # 获取url
            html_file_path = os.path.join(html_folder_path, f"{html_file_name}.html")

            if os.path.exists(html_file_path):
                html_info = extract_html_info(html_file_path, url, html_file_name)
                writer.writerow(html_info)
            else:
                print(f"Warning: HTML file {html_file_name}.html not found.")
    
    print(f"Index successfully written to {output_csv_file}")

# 主函数
def main():
    input_csv = './HtmlFile.csv'  # 输入CSV文件路径
    output_csv = './HtmlFile_index.csv'  # 输出索引CSV文件路径
    
    file_data = read_csv(input_csv)  # 读取原始HTML文件名和URL数据
    build_index_and_write_to_csv(file_data, output_csv)  # 构建索引并且写入CSV文件

if __name__ == "__main__":
    main()