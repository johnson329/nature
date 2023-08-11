import csv
import json
import os
import urllib

import requests
from lxml import etree
from loguru import logger
import pandas as pd

logger.add('nature.log', encoding='utf-8', rotation='1 MB')


class Crawler(object):
    def __init__(self):
        self.session = requests.session()
        self.headers = {
            "authority": "www.nature.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh,zh-CN;q=0.9,ja;q=0.8,zh-TW;q=0.7,zh-HK;q=0.6,ko;q=0.5,ar;q=0.4,en-US;q=0.3,en;q=0.2",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "referer": "https://www.nature.com/nature/research-articles?searchType=journalSearch&sort=PubDate&page=7960",
            "sec-ch-ua": "\"Not/A)Brand\";v=\"99\", \"Google Chrome\";v=\"115\", \"Chromium\";v=\"115\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }

    def fetch(self, url):
        return self.session.get(url, headers=self.headers).text

    def crawl_list(self, ):
        pn = 1
        while True:
            url = f'https://www.nature.com/nature/research-articles?searchType=journalSearch&sort=PubDate&page={pn}'
            raw_html = self.fetch(url)
            html = etree.HTML(raw_html)
            articles = html.xpath('//article')

            end = False
            data = []
            for article in articles:
                url = article.xpath('.//a/@href')[0]
                pdate = article.xpath('.//time/@datetime')[0]
                ab_url = urllib.parse.urljoin('https://www.nature.com/', url)
                content = self.crawl_detail(pdate, ab_url)
                logger.info("{} {}", content['ti'],content['pdate'])
                if int(pdate.split('-')[1]) == 8:
                    data.append(content)
                else:
                    end = True
                    break
            if os.path.exists('nature.csv'):
                pd.DataFrame.from_records(data).to_csv('nature.csv', index=False, mode='a', header=False)
            else:
                pd.DataFrame.from_records(data).to_csv('nature.csv', index=False, mode='a', header=True)
            if end:
                break
            pn += 1

    def crawl_detail(self, pdate, detail_url):

        html = self.fetch(detail_url)
        tree = etree.HTML(html)
        content = tree.xpath('//script[@type="application/ld+json"]')[0].text
        content = json.loads(content)
        rs = {
            'ti': content['mainEntity']['headline'],
            'abstrct': content['mainEntity']['description'],
            'authors': ' '.join([i['name'].strip() for i in content['mainEntity']['author']]),
            'doi': ''.join(content['mainEntity']['sameAs'].split('/')[-2:]),
            'pdate': pdate

        }


        return rs


if __name__ == '__main__':
    Crawler().crawl_list()
