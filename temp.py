from celery import Celery, signals, Task
from datetime import datetime, timezone, timedelta, date
from math import floor

import requests
import pymssql
import json

import twitterWebsiteSearch.TwitterWebsiteSearch as twitSearch

app = Celery('tasks')
app.config_from_object('celeryconfig')

'''

'''
@signals.worker_process_init.connect
def init_worker(**kwargs):
    global db_conn
    print('Initializing database connection for worker.')
    db_conn = get_db_conn()
 
def get_db_conn():
    keys = get_keys()
    return pymssql.connect(server=keys['server'], user=keys['user'], password=keys['password'], database=keys['database'])

def get_keys():
    with open('keys.json') as keys_file:
        keys = json.load(keys_file)
    return keys

@signals.worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    global db_conn
    if db_conn:
        print('Closing database connectionn for worker.')
        db_conn.close()

'''

'''
class TwitSearchTask(Task):
    abstract = True

    # cached requests.Session object
    _session = None

    def __init__(self):
        pass
    
    @property
    def session(self):
        if self._session is None:
            session = requests.Session()
            self._session = session

        return self._session

@app.task(base=TwitSearchTask, bind=True)
def call_api(self, query):
    twitSearch.search(query, session=self.session)



@app.task
def dispatch_twitter_query_tasks(query):
    since = date(2016,1,1)
    until = datetime.utcnow()
    for day in daterange(start_date, end_date):
        querystring = "{0} since:{1} until:{2}".format(query, since.strftime("%Y-%m-%d"), until.strftime("%Y-%m-%d"))
        

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield end_date - timedelta(n)


'''
input
    query
    start date
    end date

For each day in date range
    create a task (query,day)
        page through each page in query
            save each page to database
'''

