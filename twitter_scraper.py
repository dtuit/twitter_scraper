from TwitterWebsiteSearch import TwitterWebsiteSearch
# import pymssql
import json

def get_keys():
    with open('keys.json') as keys_file:
        keys = json.load(keys_file)
    return keys

def main():
    file_name = "tweets_AAPL_5"
    count = 0

    tw = TwitterWebsiteSearch(0)
    with open(file_name, 'w') as file:
        for result in tw.search_generator('$AAPL', '746423373266227200', '675322173448409088'):
            for tweet in result['tweets']:
                file.write(json.dumps(tweet))
                file.write('\n')
    
    # keys = get_keys()
    # try:
    #     conn = pymssql.connect(server=keys['server'], user=keys['user'], password=keys['password'], database=keys['database'])  
    # except pymssql.OperationalError as e:
    #     print(e)

if __name__ == '__main__':
    main()

