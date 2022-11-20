from pprint import pprint

import bs4


class Parser:
    """

    """

    def __init__(self, worker, season, html):
        """

        :param worker:
        :param season:
        :param html:
        """

        self.worker = worker
        self.season = season
        self.html = html

        self.data = {}

        self.do_work()

    def do_work(self):
        """

        :return:
        """
        soup = bs4.BeautifulSoup(self.html, 'html.parser')
        div = soup.find('div', {'class': 'list detail eplist'})

        for i in div.contents:
            # if type(i) is bs4.element.Tag:
            if isinstance(i, bs4.element.Tag):
                # print(type(i))
                # print(i)
                self.data_parsing(i)

        # pprint(self.data)

        if self.worker:
            self.worker.data.update({self.season: self.data})

    def data_parsing(self, i):
        """

        :param i:
        :return:
        """
        series_n = i.contents[1].contents[1].contents[1].contents[3].text
        series_n = series_n[series_n.find('Ep') + 2:]

        if self.worker and series_n == '0':
            self.worker.zero = True

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

        self.data[series_n] = full_info


if __name__ == "__main__":
    with open('imdbtst.html', encoding='utf-8') as f:
        read_data = f.read()

    Parser(None, 1, read_data)
