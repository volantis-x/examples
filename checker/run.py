# -*- coding: utf-8 -*-
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

pattern = re.compile(r'volantis|Volantis|stellar|Stellar')
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
      result = pattern.findall(data)
      if len(result) > 0:
          res['r'] = True
      else:
          res['r'] = False
          res['e'] = "NOT Volantis OR Stellar"
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

print('------- error data start ----------')
for item in error_pool:
    print(item)
print('------- error data end ----------')
print('\n')

filename='checker/output/v1/error.json'
with open(filename,'w',encoding='utf-8') as file_obj:
   json.dump(error_pool,file_obj,ensure_ascii=False)
