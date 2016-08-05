from celery import Celery, signals, Task
from datetime import datetime, timezone
import twitterWebsiteSearch.TwitterWebsiteSearch as twitSearch
import pymssql
import json
import requests
from math import floor

app = Celery('tasks')
app.config_from_object('celeryconfig')

db_conn = None

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

@app.task
def search_twitter_parallel_dispacher(query, concurrency):
    initial = twitSearch.search(query, aditional_params={'reset_error_state' : 'true'})
    min_pos = initial['_result_json'].get('min_position')
    since = 683072231455375360 # id from around 2015-12-30
    if min_pos is not None:
        # min = min_pos.split('-')[1]
        max = int(min_pos.split('-')[2])
    increment = floor( (max - since) / concurrency)
    for i in range(concurrency):
        min = max-(i*increment)
        search_twitter_page.delay(query, str(min), str(max), str(min-increment))

@app.task(base=TwitSearchTask,  bind=True)
def search_twitter_page(self, query, min=None, max=None, next_min=None):
    print(min + " " +  max + " " + next_min)
    result = twitSearch.search(query, min, max, session=self.session)
    
    if len(result['tweets']) == 0:
        pass
    else:
        if max is None:
            max = result['tweets'][0]['id_str']
        min = result['tweets'][-1]['id_str']
        if int(min) <= int(max) and int(min) > int(next_min):
            # return result['tweets']
            insert_into_DB.delay(result['tweets'])
            search_twitter_page.delay(query, min, max, next_min)

@app.task
def insert_into_DB(tweets):
    global db_conn
    if db_conn is None:
       db_conn = get_db_conn()

    cursor = db_conn.cursor()
    vals_to_insert = [(json.dumps(tweet), datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')) for tweet in tweets]
    query = "INSERT INTO [dbo].[Twitter_Staging] (InfoJson, DateInjested, DateProcessed) VALUES " + ",".join( "( %s, %s, NULL)" for n in vals_to_insert )
    flattened_vals = [item for sublist in vals_to_insert for item in sublist]
    cursor.execute(query,tuple(flattened_vals))
    db_conn.commit()

    # urls = [urlobj for tweet in tweets for urlobj in tweet.entities.urls]

def main():
    tags = ['#AAPL','#GOOG','#GOOGL','#MSFT','#BRK.A','#BRK.B','#XOM','#FB','#JNJ','#GE','#AMZN','#WFC','$AAPL','$GOOG','$GOOGL','$MSFT','$BRK.A','$BRK.B','$XOM','$FB','$JNJ','$GE','$AMZN','$WFC']
    tags.append('$BRKA')
    tags.append('$BRKB')
    tags.append('#BRKA')
    tags.append('#BRKB')
    for tag in tags:
        search_twitter_parallel_dispacher.delay(tag, 10)
    