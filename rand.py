#!/usr/bin/env python3
import os
import sys
import random
import argparse

try:
    import requests
except ImportError:
    sys.exit("You need requests. run 'pip install requests'")

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("You need BeautifulSoup. run 'pip install bs4'")

try:
    from fake_useragent import UserAgent
except ImportError:
    sys.exit("You need UserAgent. run 'pip install fake-useragent'")

parser = argparse.ArgumentParser(description='Runs Kattis problem through their test cases')
parser.add_argument('--lobound', type=float, default=None, help='the lower bound for questions')
parser.add_argument('--upbound', type=float, default=None, help='the upper bound for questions')
parser.add_argument('--qamount', type=int, default=None, help='the amount of questions wanted to fetch')

args = parser.parse_args()
lobound = args.lobound
upbound = args.upbound
n = args.qamount

if lobound is None:
    lobound = float(input('Enter lower bound: '))

if upbound is None:
    upbound = float(input('Enter upper bound: '))

if lobound > 10 or upbound > 10:
    exit(0)

if n is None:
    n = int(input('How many questions: '))

seenlist = []
if os.path.isfile('./seen.txt'):
    seenlist = [line.rstrip('\n') for line in open('/' + os.getcwd() + '/seen.txt')]
qlist = []
end = False
i = 0

while end is False:
    url = 'https://open.kattis.com/problems?page=' + str(i) + '&order=problem_difficulty'
    usa = UserAgent()
    page = requests.get(url, headers={'User-Agent':str(usa.random)})
    soup = BeautifulSoup(page.content, 'html.parser')

    table = soup.find('table', attrs={'class': 'problem_list table sortable table-responsive table-kattis center table-hover table-multiple-head-rows table-compact'})

    if table is None:
        end = True
        break

    tbody = table.find('tbody')
    questions = tbody.find_all('tr')

    for tr in questions:
        tds = tr.find_all('td')
        diff = float(tds[8].text)

        if diff > upbound:
            end = True
            break

        elif diff >= lobound and diff <= upbound:
            idurl = tds[0].find('a')['href']
            if idurl.split('/')[2] not in seenlist:
                qlist.append(idurl.split('/')[2])
    i += 1

random.shuffle(qlist)

for j in range(min(n,len(qlist))):
    os.popen('/' + os.getcwd() + '/fetch.py --id ' + qlist[j])

