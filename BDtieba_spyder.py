import re
import os
import sys
import json
import time
import random
import requests
import pandas as pd
from tqdm import tqdm
from lxml import etree
from datetime import datetime


class BDPostBar(object):
    def __init__(self, config):
        self.user_info = {}
        self.all_pages = []
        self.result = pd.DataFrame()
        self.identify_user_config(config)
        self.cookie = {'Cookie': config['cookie']}
        self.request_aim(config)

    def identify_user_config(self, config):
        try:
            query_str = config['query_str']
            cookie = config['cookie']
            if not (isinstance(query_str, str) and isinstance(cookie, str)):
                print('query_str、cookie 应该为 str 类型而不是 ' + '{}'.format(type(query_str)))
                sys.exit()
            self.user_info['查询贴吧'] = config['query_str']
            self.user_info['记录模式'] = config['write_mode']
            self.user_info['启用时间'] = datetime.today().__format__('%Y-%m-%dT%H:%M:%S')
        except Exception as error:
            print(error)
            sys.exit()

    # 获取所有的页数及其网址
    def request_aim(self, config):
        url = 'http://tieba.baidu.com/f?kw=%s&ie=utf-8&pn=0' % config['query_str']
        # print(url)
        html = self.handle_url(url)
        try:
            tail_page = html.xpath('//*[@id="frs_list_pager"]/a[@class="last pagination-item "]/@href')[0]
            tail_page = int(re.compile(r'&pn=\d+').search(tail_page).group()[4:])
            for i in range(0, tail_page + 50, 50):
                self.all_pages.append(url.strip('0') + str(i))  # 也可通过href内容获取网页链接
            print('{} 贴吧，共有 {}页'.format(config['query_str'], int(tail_page/50 + 1)))
            # print(self.all_pages)
            return self.all_pages
        except print('请检查header以及cookie\n请重试几次'):
            sys.exit(u'网页获取失败，程序退出')

    # 访问all_pages中包含的网页，n代表访问前n页，并获取相关信息
    def get_pages_info(self, n: int):
        data = pd.DataFrame(columns=['Answer', 'Title', 'Link_url', 'Author', 'Author_id', 'At_Top or Good'])
        Answer, Title, Link_url, Author, Author_id, Floors = [], [], [], [], [], []
        try:
            total_t = 0
            top_floor = 0
            for url in tqdm(self.all_pages[0: n]):
                t = random.randint(1, 10)    # 方便计时
                total_t += t
                time.sleep(t)    # 随机睡眠
                html = self.handle_url(url)
                floor = html.xpath('//*[@data-floor]/@data-floor')
                poster = html.xpath('//*[@class="tb_icon_author no_icon_author"]/@title|//*[@class="tb_icon_author "]/@title')
                poster_id = html.xpath('//*[@class="tb_icon_author no_icon_author"]/@data-field|//*[@class="tb_icon_author "]/@data-field')
                ans_num = html.xpath('//*[@title="回复"]/text()')
                tag = html.xpath('//*[@class="j_th_tit "]/text()')
                link = html.xpath('//*[@class="j_th_tit "]/@href')
                if '0' in floor:
                    top_floor = floor.count('0')
                    for i in range(len(floor)):
                        if floor[i] == '0':
                            floor[i] = 1
                        else:
                            floor[i] = 0
                else:
                    for i in range(len(floor)):
                        floor[i] = 0
                for x in range(len(floor)):
                    Answer.append(ans_num[x])
                    Title.append(tag[x])
                    Link_url.append('http://tieba.baidu.com' + link[x])
                    Author.append(poster[x][5:])
                    Author_id.append(poster_id[x][11:-1])
                    Floors.append(floor[x])
            if top_floor != 0:
                print('前%d楼为置顶层' % top_floor)
            data['Answer'] = Answer
            data['Title'] = Title
            data['Link_url'] = Link_url
            data['Author'] = Author
            data['Author_id'] = Author_id
            data['At_Top or Good'] = Floors
            self.result = data
            self.user_info['等待时间'] = total_t
            print('累计等待时间：%.2f' % total_t)
        except Exception as e:
            print(e)

    def handle_url(self, url):
        try:
            response = requests.get(url,
                                    headers=select_header(),     # 可能header问题居多
                                    cookies=self.cookie).content
            html = etree.HTML(response)
            return html
        except Exception as e:
            print('HTML Handle Error: ', e)


def select_header():
    headers_value = [
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.85 Safari/537.36 Edg/80.0.361.47",
        "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
    ]
    header_value = random.choice(headers_value)
    header = {'User-Agent': '{}'.format(header_value)}
    return header


# 确认是否在同一目录下进行操作
def identify_config_exist():
    try:
        with open(os.path.dirname(__file__) + os.sep + 'BDtieba_config.json', 'r', encoding='utf-8') as config_IO:
            print('{0}\n当前工作目录在：{1}'.format('*'*100, os.path.dirname(__file__)))
            config_json = json.load(config_IO)
            print('已加载当前目录下的BDtieba_config.json\n配置加载完毕\n{}'.format('*'*100))
            return config_json
    except Exception as error:
        print(error)
        return print('请检查是否存在 "BDtieba_config.json" （配置文件）')


def main():
    start = time.time()    # 程序开始时间
    config = identify_config_exist()    # 确认本程序是否能够在当前目录下运行，并将设置文件读取后传入config
    BD = BDPostBar(config)    # 实例化对象
    logInfo = '{}'.format(BD.user_info)    # 日志文件
    # 下面这个 5 可以更改
    BD.get_pages_info(5)    # 获取贴吧前面几页，5就是获取5页
    BD.result.to_csv('%s的结果.csv' % config['query_str'], encoding='utf-8-sig')    # 保留爬取结果
    end = time.time()    # 拟定程序结束时间
    with open(os.path.dirname(__file__) + os.sep + "UserLog.txt", 'a+') as log:    # 写入日志文件
        log.writelines(logInfo + '\n')
    print('程序执行完毕\n程序共耗时 %.3f 秒' % (end-start))    # 程序结束


if __name__ == '__main__':
    main()
