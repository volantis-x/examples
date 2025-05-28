# -*- coding: utf-8 -*-
import sys
from time import sleep, time
import requests
from bs4 import BeautifulSoup
import re
import yaml
import request
import json
import os
import myselenium

version = 'v2'
outputdir = version  # 输出文件结构变化时，更新输出路径版本
data_pool = []

def fix_label(a):
    b=["example","invalid","Maybe NOT Volantis WARNING","NETWORK ERROR","NETWORK WARNING","NOT HTTPS","NOT Volantis","🗑️ Suggest to close"]
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

def get_issue_id(a):
    for i in range(len(a)):
        #取出索引对应的值
        t=a[i]
        #判断值是否存在在序列b中
        if "#" in t:
            return t
    return "0#0"

def load_config():
    f = open('config.yml', 'r',encoding='utf-8')
    ystr = f.read()
    ymllist = yaml.load(ystr, Loader=yaml.FullLoader)
    return ymllist

def github_issuse(data_pool):
    print('\n')
    print('------- github issues start ----------')
    baselink = 'https://github.com/'
    config = load_config()
    try:
        for number in range(1, 1000):
            print("page="+str(number))
            if config['issues']['label']:
                label_plus = '+label%3A' + config['issues']['label']
            else:
                label_plus = ''
            github = myselenium.get('https://github.com/' +
                             config['issues']['repo'] +
                             '/issues?q=is%3Aopen' + str(label_plus) + '&page=' + str(number))
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
                    
                    issues_linklist = issues_soup.find_all('pre')
                    source = issues_linklist[0].text
                    issues_labels = set()
                    issues_labels_a = issues_soup.find_all('span', {'class': 'prc-Text-Text-0ima0'})
                    for i in issues_labels_a:
                      issues_labels.add(i.text.strip())
                    issues_id = get_issue_id(list(issues_labels))
                    print(issues_id)
                    issues_labels=fix_label(list(issues_labels))
                    print(issues_labels)
                    if "{" in source:
                        source = json.loads(source)
                        print(source["url"])
                        data_pool.append({'id': issues_id, 'url': source['url'], "labels": issues_labels})
                except Exception as e:
                    print(e)
                    continue
    except Exception as e:
        print(e)
        print('> end')

    print('------- github issues end ----------')
    print('\n')



github_issuse(data_pool)

pattern1 = re.compile(r'volantis|Volantis')
pattern2 = re.compile(r'l_header|l_body')
pattern3 = re.compile(r'app.js|volantis-x|pjax_')


def checker_url(item,header_ua_random=False):
    res={}
    try:
      print(item['id'])
      print(item['url'])
      # 85 老版本
      if item['id'] == "85":
        res['r'] = True
        return res
      data = request.get_data(item['url'],header_ua_random)
      if data == 'error::404':
        res['r'] = False
        res['e'] = "error::404"
        return res
      if data == 'error::not200':
        res['r'] = False
        res['e'] = "NETWORK ERROR"
        return res
      if data == 'error':
        res['r'] = False
        res['e'] = "NETWORK ERROR"
        return res
      result1 = pattern1.findall(data)
      result2 = pattern2.findall(data)
      result3 = pattern3.findall(data)

      if len(result1) > 0 and len(result2) > 0 and len(result3) > 0:
          res['r'] = True
      else:
          res['r'] = False
          res['e'] = "NOT Volantis"
          res['d'] = data
          print(data)
    except Exception as e:
        res['r'] = False
        res['e'] = "NETWORK ERROR"
    return res

def delete_labels(issue_number,labels):
  try:
    config = load_config()
    url='https://api.github.com/repos/'+config['issues']['repo']+'/issues/'+issue_number+'/labels/'+labels
    handlers={
      "Authorization": "token "+sys.argv[1],
      "Accept": "application/vnd.github.v3+json"
    }
    r=requests.delete(url=url, headers=handlers)
    print(r.text.encode("gbk", 'ignore').decode('gbk', 'ignore'))
  except Exception as e:
    print(e)


print('------- checker start ----------')
error_pool=[]
for item in data_pool:
    print(item)
    result = checker_url(item)
    if not result['r']:
        item['error'] = result['e']
        if item['error'] == "NOT Volantis":
            sleep(20)
            result = checker_url(item,True)
            if not result['r']:
              item['error'] = result['e']
              item['data'] = result['d']
              error_pool.append(item)
        else:
            error_pool.append(item)
    else:
      print("OK")
      if "NETWORK WARNING" in item['labels']:
          print("delete label NETWORK WARNING...")
          delete_labels(item['id'],"NETWORK WARNING")

print('------- checker end ----------')
print('\n')

def add_labels(issue_number,labels):
  try:
    config = load_config()
    url='https://api.github.com/repos/'+config['issues']['repo']+'/issues/'+issue_number+'/labels'
    data= labels
    handlers={
      "Authorization": "token "+sys.argv[1],
      "Accept": "application/vnd.github.v3+json"
    }
    r=requests.post(url=url,data=data,headers=handlers)
    # print(r.text.encode("gbk", 'ignore').decode('gbk', 'ignore'))
  except Exception as e:
    print(e)

def Create_an_issue_comment_invalid(issue_number,invalid_data):
  try:
    config = load_config()
    url='https://api.github.com/repos/'+config['issues']['repo']+'/issues/'+issue_number+'/comments'
    data={"body":'''**⚠️ 抱歉，Github Actions 检测到您的网站存在违规信息，现已下架。**\r\n\r\n如果您确认已经处理了违规信息，请重新提交issues.\r\n\r\n以下是 Github Actions 检测到的违规信息 [注: Github Actions 可能会触发网站防火墙]\r\n\r\n<details><summary>违规信息:</summary>\r\n\r\n```\r\n\r\n'''+invalid_data+'''\r\n\r\n```\r\n\r\n</details>\r\n\r\n'''}
    data=json.dumps(data)
    handlers={
      "Authorization": "token "+sys.argv[1],
      "Accept": "application/vnd.github.v3+json"
    }
    r=requests.post(url=url,data=data.encode(),headers=handlers)
    # print(r.text.encode("gbk", 'ignore').decode('gbk', 'ignore'))
  except Exception as e:
    print(e)

# https://docs.github.com/en/rest/reference/issues#update-an-issue
def Close_an_issue(issue_number):
  try:
    config = load_config()
    url='https://api.github.com/repos/'+config['issues']['repo']+'/issues/'+issue_number
    data='''{"state":"closed"}'''
    handlers={
      "Authorization": "token "+sys.argv[1],
      "Accept": "application/vnd.github.v3+json"
    }
    r=requests.patch(url=url,data=data.encode(),headers=handlers)
    # print(r.text.encode("gbk", 'ignore').decode('gbk', 'ignore'))
  except Exception as e:
    print(e)

print('------- error data start ----------')
for item in error_pool:
    print(item)
    if item['error'] == "NOT Volantis":
        add_labels(item['id'],'["Maybe NOT Volantis WARNING"]')
        Create_an_issue_comment_invalid(item['id'],item['data'])
        Close_an_issue(item['id'])
    if item['error'] == "NETWORK ERROR":
        add_labels(item['id'],'["NETWORK WARNING"]')
        if item['url'] == "https://" or item['url'] == "":
            add_labels(item['id'],'["invalid"]')
            Create_an_issue_comment_invalid(item['id'],"无效 URL")
            Close_an_issue(item['id'])
    if item['error'] == "error::404":
        add_labels(item['id'],'["NETWORK WARNING"]')
        add_labels(item['id'],'["invalid"]')
        Create_an_issue_comment_invalid(item['id'],"<Response [404]>")
        Close_an_issue(item['id'])
print('------- error data end ----------')
print('\n')


def mkdir(path):
    folder = os.path.exists(path)
    if not folder:
        os.makedirs(path)
        print("create dir:", path)
    else:
        print("dir exists:", path)

mkdir(outputdir)
filename = outputdir + '/error.json'
with open(filename,'w',encoding='utf-8') as file_obj:
    data = {'version': version, 'content': error_pool}
    json.dump(data, file_obj, ensure_ascii=False, indent=2)
