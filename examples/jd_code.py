import requests
import pandas as pd
import json
import time
 
def get_comments(product_id, page):
    """获取指定商品分页的评论数据"""
    url = f'https://club.jd.com/comment/productPageComments.action?callback=fetchJSON_comment98&productId={product_id}&pageSize=10&score=0&sortType=5&isShadowSku=0&fold=1&page={page}'
    
    # 发送请求
    try:
        response = requests.get(url)
        content = response.text.strip('fetchJSON_comment98();')  # 去掉callback函数名称
        comments_data = json.loads(content)  # 解析 JSON 数据
        return comments_data
    except Exception as e:
        print(f"请求错误: {e}")
        return None
 
# 示例商品ID
product_id = '100012043978'  # 以某款商品 ID 为例
 
# 初始化一个空列表，用于存储评论
all_comments = []
 
# 爬取前 10 页的评论
for page in range(1, 11):
    comments_data = get_comments(product_id, page)
    if comments_data:
        for comment in comments_data['comments']:
            all_comments.append({
                '内容': comment['content'],
                '时间': comment['creationTime'],
                '评分': comment['score']
            })
    # 控制请求频率，避免被封
    time.sleep(1)
 
# 输出爬取的评论数
print(f"成功爬取 {len(all_comments)} 条评论")