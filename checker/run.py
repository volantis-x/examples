# -*- coding: utf-8 -*-
import sys
import requests
from bs4 import BeautifulSoup
import re
import yaml
from request_data import request
import json

data_pool = []

def load_config():
    f = open('_config.yml', 'r',encoding='utf-8')
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
            github = request.get_data('https://github.com/' +
                             config['issues']['repo'] +
                             '/issues?q=is%3A' + config['issues']['state'] + str(label_plus) + '&page=' + str(number))
            soup = BeautifulSoup(github, 'html.parser')
            main_content = soup.find_all('div',{'aria-label': 'Issues'})
            linklist = main_content[0].find_all('a', {'class': 'Link--primary'})
            if len(linklist) == 0:
                print('> end')
                break
            for item in linklist:
                issueslink = baselink + item['href']
                issues_page = request.get_data(issueslink)
                issues_soup = BeautifulSoup(issues_page, 'html.parser')
                try:
                    issues_id = issues_soup.find_all('span', {'class': 'f1-light'})[0].text.strip().split('#')[1]
                    print(issues_id)
                    issues_linklist = issues_soup.find_all('pre')
                    source = issues_linklist[0].text
                    if "{" in source:
                        source = json.loads(source)
                        print(source["url"])
                        data_pool.append({'id': issues_id, 'url': source['url']})
                except:
                    continue
    except Exception as e:
        print('> end')

    print('------- github issues end ----------')
    print('\n')



github_issuse(data_pool)

pattern1 = re.compile(r'volantis|Volantis')
pattern2 = re.compile(r'l_header|l_body')

def checker_url(item):
    res={}
    try:
      print(item['id'])
      print(item['url'])
      data = request.get_data(item['url'])
      if data == 'error':
        res['r'] = False
        res['e'] = "NETWORK ERROR"
        return res
      result1 = pattern1.findall(data)
      result2 = pattern2.findall(data)
      if len(result1) > 0 and len(result2) > 0:
          res['r'] = True
      else:
          res['r'] = False
          res['e'] = "NOT Volantis"
    except Exception as e:
        res['r'] = False
        res['e'] = "NETWORK ERROR"
    return res


print('------- checker start ----------')
error_pool=[]
for item in data_pool:
    result = checker_url(item)
    if not result['r']:
        item['error'] = result['e']
        error_pool.append(item)

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

def Create_an_issue_comment_invalid(issue_number):
  try:
    config = load_config()
    url='https://api.github.com/repos/'+config['issues']['repo']+'/issues/'+issue_number+'/comments'
    data={"body":'''**⚠️ 抱歉，经过 Github Actions 检测，您的网站存在违规信息，现已下架。**\r\n\r\n如果您确认已经处理了违规信息，请重新提交issues.'''}
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
        add_labels(item['id'],'["invalid","NOT Volantis"]')
        Create_an_issue_comment_invalid(item['id'])
        Close_an_issue(item['id'])
    if item['error'] == "NETWORK ERROR":
        add_labels(item['id'],'["NETWORK WARNING"]')
print('------- error data end ----------')
print('\n')

filename='checker/output/v1/error.json'
with open(filename,'w',encoding='utf-8') as file_obj:
   json.dump(error_pool,file_obj,ensure_ascii=False,indent=4)
