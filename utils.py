import datetime
import time

from fake_headers import Headers


class Appdata:
    def __init__(self):
        self.previous_requests = {}

    def add(self, new):
        if len(self.previous_requests) == 100:
            del self.previous_requests[list(self.previous_requests.keys())[0]]
        self.previous_requests.update(new)

    def check_time(self, id):
        # неделя 604800
        return time.time() - self.previous_requests[id].launche_time < 604800

    def check_cache(self, id):
        return id in self.previous_requests and self.check_time(id)

    @property
    def reverse_list(self):
        return list(self.previous_requests.keys())[::-1]

    @property
    def year(self):
        return datetime.datetime.now().year


def fake_head():
    return Headers(headers=True).generate()


def save_html_file(html):
    name = f'{round(time.time())}.html'
    print('DEBUG_SAVE_HTML', name)
    with open(name, "w", encoding='utf-8') as file:
        file.write(html)
