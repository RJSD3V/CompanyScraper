from flask import Flask , render_template
from flask import request,url_for
from CrawlerFunctions import assemble_Content,summarize,getScreenShot,getTitle,getTree,logo_icon,crawl_emails,data_push
from urllib.request import urlopen
from urllib.error import URLError
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from collections import deque
from urllib.parse import urlsplit
import re
import pandas as pd
import json
from json import dumps,dump,JSONEncoder
import pickle


#BrainsFeed Project Assignment
#Raajas Sode

app = Flask(__name__)


@app.route('/')
def docs():
    return render_template('hello.html')
@app.route('/get', methods = ['GET'])
def fetch_Page():
    key = 'brainsfeed1234'
    auth = request.args.get('key')
    if(auth == key):
        link = request.args.get('url')
        try:

            raw = assemble_Content(link)
        except(ValueError):
            return '<h1>Sorry, Something went wrong, Try entering the full URL</h1>'
        response = json.dumps(raw,cls = JSONEncoder)

        return response
    else:
        return '<h1> Sorry, Enter the Correct Key in the API Call</h1>'

@app.route('/push')
def push():
    key = 'brainsfeed1234'
    auth = request.args.get('key')
    link = request.args.get('url')
    if(auth == key):
        try:
            raw = assemble_Content(link)
            data_push(link,raw)
            return '<h1>Data Pushed Successfully</h1>'
        except:
            return '<h1> Sorry, Something Went Wrong, Enter the Correct </h1>'
    else:
        return '<h1> Sorry, Enter the Correct Key in the API Call</h1>'

if __name__ == "__main__":
    app.run(debug=True)


