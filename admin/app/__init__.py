
from flask import Flask
from flask import request
from flask_bootstrap import Bootstrap

import os
#from app.config import Config



app = Flask(__name__)
#app.config.from_object(Config)

SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

bootstrap = Bootstrap(app)

from app import routes






