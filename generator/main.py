# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import os
import request
import json
import config
import myselenium

version = 'v2'
outputdir = version  # 输出文件结构变化时，更新输出路径版本
filenames = []
json_pool = []
baselink = 'https://github.com/'

def fix_label(a):
    b=["example","invalid","Maybe NOT Volantis WARNING","NETWORK ERROR","NETWORK WARNING","NOT HTTPS","NOT Volantis","🗑️ Suggest to close","SKIP"]
    #定义空列表
    c=[]
    #range(len(a))取的为列表a的索引，根据a的
    for i in range(len(a)):
        #取出索引对应的值
        t=a[i]
        #判断值是否存在在序列b中
        if t in b:
           #如果序列在b中，则写入序列c
           c.append(t)
    return c




def mkdir(path):
    folder = os.path.exists(path)
    if not folder:
        os.makedirs(path)
        print("create dir:", path)
    else:
        print("dir exists:", path)

def getData(repo,parameter,sort,data_pool,json_pool):
    try:
        for number in range(1, 100):
            linklist = []
            print('page:', number)
            url = 'https://github.com/' + repo + '/issues?page=' + str(number) + '&q=is%3Aopen'
            if parameter:
                url = url + parameter
            if sort:
                url = url + '+sort%3A' + sort
            print('parse:', url)
            github = myselenium.get(url)
            soup = BeautifulSoup(github, 'html.parser')
            linklist = soup.find_all('a', {'data-testid': 'issue-pr-title-link'})
            if len(linklist) == 0:
                print('> end')
                break
            for item in linklist:
                issueslink = baselink + item['href']
                issues_page = request.get_data(issueslink)
                issues_soup = BeautifulSoup(issues_page, 'html.parser')
                try:

                    issues_labels = set()
                    issues_labels_a = issues_soup.find_all('span', {'class': 'prc-Text-Text-0ima0'})
                    for i in issues_labels_a:
                      issues_labels.add(i.text.strip())
                    issues_labels=fix_label(list(issues_labels))
                    print(issues_labels)
                    if "NETWORK WARNING" in issues_labels and "SKIP" not in issues_labels:
                        print("skip this.")
                        continue

                    
                    issues_linklist = issues_soup.find_all('pre')
                    source = issues_linklist[0].text
                    if "{" in source:
                        source = json.loads(source)
                        print(source)
                        data_pool.append(source)
                except:
                    continue
    except Exception as e:
        print('> end')
    json_pool.append(data_pool)

def github_issuse(json_pool):
    print('\n')
    print('------- github issues start ----------')
    cfg = config.load()
    filter = cfg['issues']

    if not filter["groups"]:
        # 如果没有配置groups，全部输出至data.json
        data_pool = []
        filenames.append("data")
        parameter='+label%3A' + (filter["label"] if filter["label"] else '')
        getData(filter["repo"],parameter,filter["sort"],data_pool,json_pool)

    else:
        # 如果配置多个了groups，按照分组抓取并输出
        for group in filter["groups"]:
            print('start of group:', group)
            data_pool = []
            filenames.append(group)
            parameter='+label%3A' + (filter["label"] if filter["label"] else '') + '+label%3A' + group
            getData(filter["repo"],parameter,filter["sort"],data_pool,json_pool)
            print("end of group:", group)

    print('------- github issues end ----------')
    print('\n')


# 友链规则
github_issuse(json_pool)
mkdir(outputdir)
full_path = []
i = 0
for filename in filenames:
    full_path.append(outputdir + '/' + filename + '.json')
    with open(full_path[i], 'w', encoding='utf-8') as file_obj:
        data = {'version': version, 'content': json_pool[i]}
        json.dump(data, file_obj, ensure_ascii=False, indent=2)
    i += 1
