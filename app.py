import os
import requests
import operator
import re
import nltk
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from nltk.corpus import stopwords
from collections import Counter
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

from models import *

@app.route('/', methods=['GET', 'POST'])
def index():
	errors = []
	results = {}
	if request.method == "POST":
		try:
			url = request.form['url']
			r = requests.get(url)
		except:
			errors.append(
				"Unable to get URL. Please make sure it's valid and try again"
			)
	return render_template('index.html', errors=errors, results=results)

if __name__ == '__main__':
	app.run()
