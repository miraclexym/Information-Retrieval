import jieba
import csv
import math
from collections import defaultdict
import pickle

# 增加字段大小限制，设置为更大的值（比如 10MB）
csv.field_size_limit(10000000)

# 读取 CSV 文件
def read_csv(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return [row for row in reader]

# 中文分词
def tokenize(text):
    return list(jieba.cut(text))

# 计算文档的TF
def compute_tf(doc):
    tf = defaultdict(int)
    for word in doc:
        tf[word] += 1
    # 将词频转化为TF
    total_words = len(doc)
    for word in tf:
        tf[word] /= total_words
    return tf

# 计算所有文档的IDF
def compute_idf(documents):
    idf = defaultdict(int)
    total_docs = len(documents)
    
    for doc in documents:
        unique_words = set(doc)
        for word in unique_words:
            idf[word] += 1
    
    # 计算IDF
    for word in idf:
        idf[word] = math.log(total_docs / (1 + idf[word]))  # 加1防止除零
    
    return idf

# 构建倒排索引
def build_inverted_index(documents):
    inverted_index = defaultdict(list)
    doc_tfs = []
    
    # 遍历文档
    for doc_id, doc in enumerate(documents):
        if doc_id % 500 == 0:  # 每500个文档输出一次
            print(f"正在处理第 {doc_id} 个文档...")
        tf = compute_tf(doc)
        doc_tfs.append(tf)
        for word in tf:
            inverted_index[word].append((doc_id, tf[word]))
    
    # 计算IDF
    idf = compute_idf(documents)
    
    # 保存倒排索引和TF-IDF计算结果
    return inverted_index, doc_tfs, idf

# 保存倒排索引到文件
def save_index(inverted_index, doc_tfs, idf, filename="Text_Index.pkl"):
    with open(filename, 'wb') as f:
        pickle.dump((inverted_index, doc_tfs, idf), f)

if __name__ == "__main__":
    # 读取数据
    print("开始读取 CSV 文件...")
    documents = read_csv('Html_Content.csv')
    print(f"已读取 {len(documents)} 行数据。")
    
    # 提取每个文档的文本内容（使用anchors和body）
    docs = []
    for doc_id, doc in enumerate(documents):
        text = doc['anchors'] + " " + doc['body']
        words = tokenize(text)
        docs.append(words)
        
        # 每500个文档输出一次
        if doc_id % 500 == 0:
            print(f"已处理 {doc_id} 个文档...")
    
    # 构建倒排索引
    print("开始构建倒排索引...")
    inverted_index, doc_tfs, idf = build_inverted_index(docs)
    
    # 保存倒排索引
    print("开始保存倒排索引...")
    save_index(inverted_index, doc_tfs, idf)
    print("倒排索引构建并保存完成")