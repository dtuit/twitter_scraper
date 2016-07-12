import TwitterWebsiteSearch
import pymssql
import json
from celery import Celery

def get_keys():
    with open('keys.json') as keys_file:
        keys = json.load(keys_file)
    return keys

def main():
    keys = get_keys()
    try:
        conn = pymssql.connect(server=keys['server'], user=keys['user'], password=keys['password'], database=keys['database'])
        cursor = conn.cursor()
        cursor.execute('Select @@Version')
        row = cursor.fetchone()

        print(row)
    except pymssql.OperationalError as e:
        print(e)

if __name__ == '__main__':
    main()

