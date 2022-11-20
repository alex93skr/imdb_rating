import os
import sys

print('imdb.wsgi init')

#sys.path.insert(0, '/var/www/nextrue/app')

#activate_this = '/var/www/nextrue/venv/bin/activate_this.py'
#with open(activate_this) as file_:
#    exec(file_.read(), dict(__file__=activate_this))

#from hello import app
from imdb_flask import app


#if __name__ == "__main__":
#    app.run()