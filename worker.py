import statistics
import threading
import time
from pprint import pprint

import requests
from bs4 import BeautifulSoup

from series_parser import Parser
from utils import fake_head

DEBUG = False
INDENT = '              '

class Worker:
    def __init__(self, id):
        self.id = id
        self.data = {}
        self.title = ''
        self.zero = False
        self.table = ''
        self.launche_time = time.time()
        self.search_time = None
        self.err = None

        # self.do_work()
        # self.table_creation()

        try:
            start = time.perf_counter_ns()
            self.do_work()
            if DEBUG: pprint(self.data)

            self.table_creation()
            if DEBUG: pprint(self.table)

            end = time.perf_counter_ns()
            self.search_time = round((end - start) / 1000000000, 2)
        except Exception as err:
            self.err = err
            if DEBUG: print('ERR', err)

    def do_work(self):

        # чек первой страницы
        url = f'https://www.imdb.com/title/{self.id}/episodes?season=1'
        r = requests.get(url, headers=fake_head())
        # r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')

        if soup.title.text == '404 Error - IMDb':
            raise Exception('404 Error - IMDb')

        # title = title.replace('\t', '').replace('\n', '').strip().replace(' ', ' ')
        # self.title = title.replace(' - Season 1 - IMDb', '')

        title = soup.find('h3', {'itemprop': 'name'}).text
        self.title = ' '.join(title.split())

        # собрать список сезонов
        # select_bySeason = soup.find('select', {'id': 'bySeason'})
        # max_season = select_bySeason.contents[len(select_bySeason.contents) - 2].attrs['value']

        select_bySeason = soup.find('select', {'id': 'bySeason'})
        all = select_bySeason.find_all('option', {'value': True})
        # print([n.attrs['value'] for n in all])
        max_season = max([int(n.attrs['value']) for n in all])

        if DEBUG: print('max_season', max_season)

        # спарсить данные первого сезона
        Parser(self, 1, r.text)

        # остальные сезоны по потокам:

        if max_season == 1:
            return

        threads = []

        for season in range(2, int(max_season) + 1):
            t = Worker_thread(self, season)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def update_safe_html(self, st):
        self.table = f'{self.table}{st}\n'

    def table_creation(self):
        def print_bg(n):
            # цвет фона в зависимости от рейтинга
            if n >= 9: return self.update_safe_html(f'{INDENT}<td bgcolor="#3A751A">{n}</td>')
            if n >= 8: return self.update_safe_html(f'{INDENT}<td bgcolor="#8FC379">{n}</td>')
            if n >= 7: return self.update_safe_html(f'{INDENT}<td bgcolor="#FFD95E">{n}</td>')
            if n == 0.0: return self.update_safe_html(f'{INDENT}<td bgcolor="#FFFFFF">{n}</td>')

            return self.update_safe_html(f'{INDENT}<td bgcolor="#E56469">{n}</td>')

        max_season = len(self.data)

        min_series = 0 if self.zero else 1
        max_series = max([len(self.data[i]) for i in self.data])

        # print(max_series)
        # print(self.zero)

        rowspan = max_series + 1 if self.zero else max_series

        # HTML NEW

        # сезоны
        self.update_safe_html(f'{INDENT}<tr>')
        self.update_safe_html(f'{INDENT}<td class="black_bg" colspan="2">&nbsp;</td>')
        self.update_safe_html(f'{INDENT}<td class="black_bg" colspan="{max_season}">с е з о н ы</td>')
        self.update_safe_html(f'{INDENT}</tr>')

        # сезоны п/п
        self.update_safe_html(f'{INDENT}<tr>')
        self.update_safe_html(f'{INDENT}<td class="black_bg" colspan="2">&nbsp;</td>')
        for season in range(1, max_season + 1):
            self.update_safe_html(f'{INDENT}<td class="black_bg">{season}</td>')
        self.update_safe_html(f'{INDENT}</tr>')

        # серии
        for series in range(min_series, max_series + 1):
            self.update_safe_html(f'{INDENT}<tr>')
            for season in range(max_season + 1):
                if season == 0:
                    if series == min_series:
                        self.update_safe_html(
                            f'{INDENT}<td class="black_bg" rowspan="{rowspan}">с<br>е<br>р<br>и<br>и</td>')
                    self.update_safe_html(f'{INDENT}<td class="black_bg">{series}</td>')
                else:
                    try:
                        n = float(self.data[season][str(series)]["rating"])
                        print_bg(n)
                    except:
                        self.update_safe_html(f'{INDENT}<td>&nbsp;</td>')
            self.update_safe_html(f'{INDENT}</tr>')

        # подвал скип
        self.update_safe_html(f'{INDENT}<tr>')
        self.update_safe_html(f'{INDENT}<td class="black_bg" colspan="2">&nbsp;</td>')
        self.update_safe_html(f'{INDENT}<td colspan="{max_season}">&nbsp;</td>')
        self.update_safe_html(f'{INDENT}</tr>')

        # средний
        self.update_safe_html(f'{INDENT}<tr>')
        self.update_safe_html(f'{INDENT}<td class="black_bg" colspan="2">средний</td>')
        for season in range(1, max_season + 1):
            # n = [float(self.data[str(season)][str(series)]["rating"]) for series in self.data[str(season)]]

            series_arr = []

            for series in self.data[season]:
                n = float(self.data[season][series]["rating"])
                if n != 0.0:
                    series_arr.append(n)

            if series_arr != []:
                n = round(statistics.mean(series_arr), 2)
                print_bg(n)
            else:
                print_bg(0.0)

        self.update_safe_html(f'{INDENT}</tr>')


class Worker_thread(threading.Thread):
    """

    """

    def __init__(self, worker, season):
        """

        :param worker:
        :param season:
        """
        self.worker = worker
        self.season = season
        threading.Thread.__init__(self)

    def run(self):
        """

        :return:
        """

        url = f'https://www.imdb.com/title/{self.worker.id}/episodes?season={self.season}'
        r = requests.get(url, headers=fake_head())
        # r = requests.get(self.url, headers=fake_head())
        Parser(self.worker, self.season, r.text)


if __name__ == "__main__":
    Worker('tt0303461')
