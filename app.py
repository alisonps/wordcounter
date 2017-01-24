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
from rq import Queue
from rq.job import Job
from worker import conn
from flask import jsonify

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

q = Queue(connection=conn)

from models import *

@app.route('/', methods=['GET', 'POST'])
def index():
	results = {}
	if request.method == "POST":
		url = format_url(request.form['url'])
		job = q.enqueue_call(
            func=count_and_save_words, args=(url,), result_ttl=5000
		)
		print(job.get_id())
	return render_template('index.html', results=results)

@app.route("/results/<job_key>", methods=['GET'])
def get_results(job_key):
	job = Job.fetch(job_key, connection=conn)
	if job.is_finished:
		result = Result.query.filter_by(id=job.result).first()
		results = sorted(
			result.result_no_stop_words.items(),
			key=operator.itemgetter(1),
			reverse=True
		)
		return jsonify(results), 200
	else:
		return "Nay!", 202


def parse_words_from_text(raw_text):
	tokens = nltk.word_tokenize(raw_text)
	text = nltk.Text(tokens)
	non_punctuation = re.compile('.*[A-Za-z].*')
	return [word for word in text if non_punctuation.match(word)]

def count_non_stop_words(words):
	stop_words = set(stopwords.words('english'))
	non_stop_words = [word for word in words if word.lower() not in stop_words]
	return Counter(non_stop_words)

def format_url(url):
	contains_https = re.compile('https?:\/\/')
	if not contains_https.match(url):
		return "http://" + url
	else:
		return url

def count_and_save_words(url):
	errors = []
	try:
		r = requests.get(url)
	except:
		errors.append(
			"Unable to get URL. Please make sure it's valid and try again"
		)
		return {"error": errors}

	raw_text = BeautifulSoup(r.text, 'html.parser').get_text()
	nltk.data.path.append('./nltk_data/')
	raw_words = parse_words_from_text(raw_text)
	raw_words_count = Counter(raw_words)
	non_stop_words_count = count_non_stop_words(raw_words)

	try:
		result = Result(
			url=url,
			result_all=raw_words_count,
			result_no_stop_words=non_stop_words_count
		)
		db.session.add(result)
		db.session.commit()
		return result.id
	except Exception, e:
		errors.append(str(e))
		errors.append("Unable to add item to database.")

if __name__ == '__main__':
	app.run()
