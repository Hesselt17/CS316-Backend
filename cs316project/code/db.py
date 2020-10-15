from flask import Flask

from sqlalchemy import *

from flask_cors import CORS

def connect():
    # connect to db
    engine = create_engine('postgresql://postgres:cs316@vcm-17053.vm.duke.edu:5432/userdesign', echo=True) # if this doesn't work, try: 'postgresql+psycopg2://michaela:cs316@vcm-17053.vm.duke.edu:5432/userdesign'
    connection = engine.connect()
    metadata = MetaData()

    # Init app
    app = Flask(__name__)
    cors = CORS(app)  # This is what allows for this backend to enable CORS (webbrowser blocking loading data)
    app.secret_key = 'julia'  # what is this used for?
