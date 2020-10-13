# -*- coding: utf-8 -*-
#############################################################

import os
import re
import statistics
import time
import threading
import requests
import bs4
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect
from jinja2 import Template
from fake_headers import Headers

app = Flask(__name__, template_folder='', static_folder='')


#############################################################


def fake_head():
    return Headers(headers=True).generate()


class Appdata:
    def __init__(self):
        self.previous_requests = {}

    def add(self, new):
        if len(self.previous_requests) == 100:
            del self.previous_requests[list(self.previous_requests.keys())[0]]
        self.previous_requests.update(new)

    @property
    def reverse_list(self):
        return list(self.previous_requests.keys())[::-1]


class Parser(threading.Thread):

    def __init__(self, caller, season, url):
        self.caller = caller
        self.season = season
        self.url = url
        threading.Thread.__init__(self)

    def run(self):
        # url = f'https://www.imdb.com{self.url}'

        r = requests.get(self.url, headers=fake_head())
        # r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        # title = soup.title.text

        div = soup.find('div', {'class': 'list detail eplist'})

        for i in div.contents:
            # if type(i) is bs4.element.Tag:
            if isinstance(i, bs4.element.Tag):
                # print(type(i))

                series_n = i.contents[1].contents[1].contents[1].contents[3].text
                series_n = series_n[series_n.find('Ep') + 2:]

                if series_n == '0':
                    self.caller.zero = True

                try:
                    series_date = i.find('div', {'class': 'airdate'}).text.replace('\n', '').strip()
                except:
                    series_date = ''

                try:
                    series_rating = i.find('span', {'class': 'ipl-rating-star__rating'}).text.replace('\n', '').strip()
                except:
                    series_rating = '0'

                try:
                    series_votes = i.find('span', {'class': 'ipl-rating-star__total-votes'}).text.replace('\n',
                                                                                                          '').strip()
                except:
                    series_votes = ''

                try:
                    series_title = i.find('a', {'itemprop': 'name'}).text.replace('\n', '').strip()
                except:
                    series_title = ''

                full_info = {
                    'date': series_date,
                    'rating': series_rating,
                    'votes': series_votes,
                    'title': series_title
                }

                # print('full_info', full_info)

                if self.season not in self.caller.data:
                    self.caller.data.update({self.season: {}})

                self.caller.data[self.season].update({series_n: full_info})


class Worker:
    def __init__(self, id):
        self.id = id
        self.data = {}
        self.title = None
        self.zero = False
        self.table = ''
        self.search_time = None
        self.err = None

        try:
            start = time.perf_counter_ns()
            self.do_work()
            self.table_creation()
            end = time.perf_counter_ns()
            self.search_time = round((end - start) / 1000000000, 2)
        except Exception as err:
            self.err = err

    def update_safe_html(self, st):
        self.table = f'{self.table}{st}\n'

    def do_work(self):
        url = f'https://www.imdb.com/title/{self.id}/'
        r = requests.get(url, headers=fake_head())
        # r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.title.text

        if title == '404 Error - IMDb':
            raise Exception(title)

        self.title = title

        try:
            div = soup.find('div', {'class': 'seasons-and-year-nav'})
        except:
            raise Exception('нету сезонов')

        # seasons = div.contents[7].findAll('a')
        mex_season = div.contents[7].findAll('a')[0].text

        threads = []

        for n in range(1, int(mex_season) + 1):
            # print(f'https://www.imdb.com/title/{self.id}/episodes?season={n}')
            t = Parser(self, str(n), f'https://www.imdb.com/title/{self.id}/episodes?season={n}')
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def table_creation(self):
        def print_bg(n):
            if n >= 9: return self.update_safe_html(f'<td bgcolor="#3A751A">{n}</td>')
            if n >= 8: return self.update_safe_html(f'<td bgcolor="#8FC379">{n}</td>')
            if n >= 7: return self.update_safe_html(f'<td bgcolor="#FFD95E">{n}</td>')
            return self.update_safe_html(f'<td bgcolor="#E56469">{n}</td>')

        max_season = len(self.data)
        min_series = 0 if self.zero else 1
        max_series = max([len(self.data[i]) for i in self.data])

        # print(max_series)
        # print(self.zero)

        rowspan = max_series + 1 if self.zero else max_series

        # HTML NEW

        # сезоны
        self.update_safe_html('<tr>')
        self.update_safe_html(f'<td class="black_bg" colspan="2">&nbsp;</td>')
        self.update_safe_html(f'<td class="black_bg" colspan="{max_season}">с е з о н ы</td>')
        self.update_safe_html('</tr>')

        # сезоны п/п
        self.update_safe_html('<tr>')
        self.update_safe_html(f'<td class="black_bg" colspan="2">&nbsp;</td>')
        for season in range(1, max_season + 1):
            self.update_safe_html(f'<td class="black_bg">{season}</td>')
        self.update_safe_html('</tr>')

        # серии
        for series in range(min_series, max_series + 1):
            self.update_safe_html('<tr>')
            for season in range(max_season + 1):
                if season == 0:
                    if series == min_series:
                        self.update_safe_html(f'<td class="black_bg" rowspan="{rowspan}">с<br>е<br>р<br>и<br>и</td>')
                    self.update_safe_html(f'<td class="black_bg">{series}</td>')
                else:
                    try:
                        n = float(self.data[str(season)][str(series)]["rating"])
                        print_bg(n)
                    except:
                        self.update_safe_html(f'<td>&nbsp;</td>')
            self.update_safe_html('</tr>')

        # подвал скип
        self.update_safe_html('<tr>')
        self.update_safe_html(f'<td class="black_bg" colspan="2">&nbsp;</td>')
        self.update_safe_html(f'<td colspan="{max_season}">&nbsp;</td>')
        self.update_safe_html('</tr>')

        # средний
        self.update_safe_html('<tr>')
        self.update_safe_html('<td class="black_bg" colspan="2">средний</td>')
        for season in range(1, max_season + 1):
            n = [float(self.data[str(season)][str(series)]["rating"]) for series in self.data[str(season)]]
            n = round(statistics.mean(n), 2)
            print_bg(n)
        self.update_safe_html('</tr>')


#############################################################

#@app.route('/qqqqqqqq')
#def hello1():
#    return redirect("https://nextrue.ru/imdb", code=301)


@app.route('/', methods=['GET'])
def index():
    id = request.args.get('id')
    # print(id)

    if (id is None) or (id == ''):
        return render_template('imdb.html', appdata=appdata)

    id = re.search(r'tt\d{6,11}', id)
    if not id:
        err_text = 'что-то не то пишете...'
        return render_template('imdb.html', TABLE=True, err=err_text, appdata=appdata)
    else:
        id = id.group(0)
        if id in appdata.previous_requests:
            worker = appdata.previous_requests[id]
        else:
            worker = Worker(id)
            if worker.err is None:
                appdata.add({id: worker})
        return render_template('imdb.html', TABLE=True, worker=worker, err=worker.err, appdata=appdata)


#############################################################

if __name__ == "__main__":

    appdata = Appdata()

    if "HEROKU" in list(os.environ.keys()):
        app.run(host="0.0.0.0", port=os.environ.get('PORT', 5000))
    else:
        # app.run()
        app.run(use_reloader=False, debug=True)

#############################################################
