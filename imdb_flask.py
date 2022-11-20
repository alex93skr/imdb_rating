import re
from pprint import pprint

from flask import Flask, render_template, request

from utils import Appdata
from worker import Worker

#############################################################

"""

IMDB
запрос идет в воркера
    воркер запускает парсер первого сезона
    из первого сезона ссылки на остальные сезоны
воркер собирает таблицу

"""

app = Flask(__name__, template_folder='', static_folder='static')

appdata = Appdata()


# @app.route('/qqqqqqqq')
# def hello1():
#    return redirect("https://nextrue.ru/imdb", code=301)


@app.route('/', methods=['GET'])
def index():
    id = request.args.get('id')
    # print(id)

    if id is None:
        return render_template('imdb.html', appdata=appdata, err=None)

    id = re.search(r'tt\d{6,12}', id)
    if not id:
        err_text = 'ошибка в ID'
        return render_template('imdb.html', appdata=appdata, err=err_text)

    else:
        id = id.group(0)
        # if id in appdata.previous_requests:
        if appdata.check_cache(id):
            worker = appdata.previous_requests[id]
        else:
            worker = Worker(id)
            if worker.err is None:
                appdata.add({id: worker})
        return render_template('imdb.html', appdata=appdata, worker=worker, err=worker.err)


@app.route('/debug', methods=['GET'])
def debug():
    # print('debug')

    for i in appdata.previous_requests:
        print(i)
        pprint(appdata.previous_requests[i].data)

    return '123'


#############################################################

if __name__ == "__main__":
    app.run(debug=True)

#############################################################
