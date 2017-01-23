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
		if r:
			raw_text = BeautifulSoup(r.text, 'html.parser').get_text()
			nltk.data.path.append('./nltk_data/')
			raw_words = parse_words_from_text(raw_text)
			raw_words_count = Counter(raw_words)
			non_stop_words_count = count_non_stop_words(raw_words)
			results = sorted(
				non_stop_words_count.items(),
				key = operator.itemgetter(1),
				reverse = True
			)
			try:
				result = Result(
					url=url,
					result_all=raw_words_count,
					result_no_stop_words=non_stop_words_count
				)
				db.session.add(result)
				db.session.commit()
			except Exception, e:
				errors.append(str(e))
				errors.append("Unable to add item to database.")
	return render_template('index.html', errors=errors, results=results)

def parse_words_from_text(raw_text):
	tokens = nltk.word_tokenize(raw_text)
	text = nltk.Text(tokens)
	non_punctuation = re.compile('.*[A-Za-z].*')
	return [word for word in text if non_punctuation.match(word)]

def count_non_stop_words(words):
	stop_words = set(stopwords.words('english'))
	non_stop_words = [word for word in words if word.lower() not in stop_words]
	return Counter(non_stop_words)

if __name__ == '__main__':
	app.run()
