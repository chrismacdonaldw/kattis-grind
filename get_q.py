#!/usr/bin/env python3
import os
import shutil
import pathlib
import requests
import argparse
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

parser = argparse.ArgumentParser(description='Fetches random Kattis Questions')
parser.add_argument('--id', type=str, default='_NONE_', help='id of problem to fetch')
args = parser.parse_args()
qid = args.id

if qid == '_NONE_':
    qid = input('Enter ID: ')
if os.path.isdir('./' + qid):
    print('This problem already exists.')
    exit(1)
url = 'http://open.kattis.com/problems/' + qid
usa = UserAgent()

page = requests.get(url, headers={'User-Agent':str(usa.random)})
soup = BeautifulSoup(page.content, 'html.parser')

tableinp = soup.find_all('table', attrs={'class': 'sample'})
pathlib.Path(qid).mkdir(parents=True, exist_ok=True)

htmlfile = soup
for section in htmlfile.find_all('section', {'class': 'box clearfix main-content problem-sidebar'}): section.decompose()
for div in htmlfile.find_all('div', {'class':['wrap', 'description','footer','problem-download','footer-powered col-md-8']}): div.decompose()
for img in htmlfile.find_all('img'): img.decompose()
for a in htmlfile.find_all('a'): a.decompose()

pathlib.Path(qid + '/' + qid + '.html').write_text(str(htmlfile))

i = 0
for sample in tableinp:
    tablestd = sample.find_all('pre')
    pathlib.Path(qid + '/input' + str(i + 1)).write_text(tablestd[0].text)
    pathlib.Path(qid + '/output' + str(i + 1)).write_text(tablestd[1].text)
    i += 1

src = os.curdir
dst = os.path.join(src, qid)
cpp = os.path.join(src, 'template.cpp')

shutil.copy(cpp, dst)

dstfile = os.path.join(dst,'template.cpp')
newfile = os.path.join(dst,'_' + qid + '.cpp')
os.rename(dstfile, newfile)
