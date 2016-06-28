import sys
import requests
from requests import Request, Session
from bs4 import BeautifulSoup
from time import sleep
import json

__author__ = 'Darren Tuit'

class TwitterWebsiteSearch():

    def __init__(self, rate_delay, error_delay=5, timeout=5, retry_limit=4, continue_on_empty_result=True):
        self.rate_delay = rate_delay
        self.error_delay = error_delay
        # TODO: impl timeout and retry
        self.timeout = timeout
        self.retry_limit = retry_limit
        self.continue_on_empty_result = continue_on_empty_result

        self.base_url = 'https://twitter.com/i/search/timeline'
    
    # TODO account for the f param f=tweets, f=news, f=videos
    def search_generator(self, query, min_tweet_id=None, max_tweet_id=None):
        s = Session()
        max_position = None
        
        # When resuming Get the starting point 
        if min_tweet_id is not None and max_tweet_id is not None:
            max_position = self.encode_max_postion_param(min_tweet_id, max_tweet_id)

        # Execute inital request
        request = self.prepare_request(self.base_url, query, max_position)
        result_json = self.execute_request(request)
        
        while result_json is not None and result_json['items_html'] is not None:
            
            tweets = self.parse_tweets(result_json['items_html']) 
            
            if len(tweets) == 0:
                if not self.continue_on_empty_result:
                    print('No tweets returned terminating program')
                    break
                else:
                    # Sometimes the API stops returning tweets even when there are more
                    # we can try to find these tweets by modifying the max_position parameter.
                    int_max_id = int(max_tweet_id)
                    # int_min_id = int(min_tweet_id)
                    # found_new_position = False
                    for x in range(8, len(max_tweet_id)):
                        max_to_try = int_max_id - 10**x
                        max_position = self.encode_max_postion_param(min_tweet_id, str(max_to_try))
                        request = self.prepare_request(self.base_url, query, max_position)
                        result_json = self.execute_request(request)
                        tweets = self.parse_tweets(result_json['items_html'])
                        if len(tweets) > 0:
                            break
                    else:
                        # if we didnt find any point to continue from break anyway.
                        break
            
            if min_tweet_id is None:
                min_tweet_id = tweets[0]['id_str']
            
            # Yield the result of each request
            yield{
                'request': request,
                'result': result_json,
                'tweets': tweets
            }

            max_tweet_id = tweets[-1]['id_str']
            if min_tweet_id is not max_tweet_id:
                max_position = self.encode_max_postion_param(min_tweet_id, max_tweet_id)

                request = self.prepare_request(self.base_url, query, max_position)
                sleep(self.rate_delay)
                result_json = self.execute_request(request)
            # else:
            #     print("min_tweet: {0} equals max_tweet: {1}".format(min_tweet, max_tweet))
            #     print("terminating program")
            #     break
    
    @staticmethod
    def encode_max_postion_param(min, max):
        return "TWEET-{0}-{1}".format(max, min)

    def execute_request(self, preparedRequest):
        try:
            s = Session()
            result = s.send(preparedRequest)
            print(preparedRequest.url)
            result_json = result.json()
            return result_json
        except requests.exceptions.Timeout as e:
            print(e.message)
            print("Sleeping for {:d}".format(self.error_delay))
            sleep(self.error_delay)
            return self.execute_request(preparedRequest)

    @staticmethod
    def prepare_request(url, query, max_position=None):
        payload = { 'q' : query }
        if max_position is not None:
            payload['max_position'] = max_position
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/29.0.1547.65 Chrome/29.0.1547.65 Safari/537.36',
            'Accept-Encoding' : 'gzip, deflate, sdch, br'
        }
        req = Request('GET', url, params=payload, headers=headers)
        return req.prepare()
    
    @classmethod
    def parse_tweets(cls, items_html):
        tweets = []
        soup = BeautifulSoup(items_html, "lxml")

        for li in soup.findAll('li', attrs={'class':'js-stream-item'}):

            # Check if is a tweet otherwise skip
            if 'data-item-id' not in li.attrs:
                continue
            #TODO change id_str to integer reresentation id.
            tweet = {
                'created_at' : None,
                'id_str' : li['data-item-id'],
                'text' : None,
                'entities': {},
                'user' : {
                    'id_str' : None, 
                    'name' : None,
                    'screen_name': None,
                    'profile_image_url': None,
                    'verified': False
                    },
                'retweet_count' : 0,
                'favorite_count' : 0
                }
            entities = {
                'hashtags': [],
                'symbols':[],
                'user_mentions':[],
                'urls':[],
            }

            # tweet text 
            text_p = li.find('p', class_="tweet-text")
            if text_p is not None:
                tweet['text'] = text_p.get_text()
            
            # user details
            user_div = li.find('div' , class_="tweet")
            if user_div is not None:
                tweet['user']['id_str'] = cls._extract_attr_value(user_div, 'data-user-id')
                tweet['user']['name'] = cls._extract_attr_value(user_div, 'data-name')
                tweet['user']['screen_name'] = cls._extract_attr_value(user_div, 'data-screen-name')
            
            user_img = li.find('img', class_="avatar")
            if user_img is not None:
                tweet['user']['profile_image_url'] = cls._extract_attr_value(user_img, 'src')

            user_verifed_span = li.find('span', class_="Icon--verified")
            if user_verifed_span is not None:
                tweet['user']['verified'] = True

            # tweet date
            date_span = li.find('span', class_="_timestamp")
            if date_span is not None:
                tweet['created_at'] = int(cls._extract_attr_value(date_span, 'data-time-ms'))
            
            # retweet count
            retweet_span = li.select("span.ProfileTweet-action--retweet > span.ProfileTweet-actionCount")
            if len(retweet_span) > 0:
                tweet['retweet_count'] = int(cls._extract_attr_value(retweet_span[0], 'data-tweet-stat-count'))

            # favourite count
            fav_span = li.select("span.ProfileTweet-action--favorite > span.ProfileTweet-actionCount")
            if len(fav_span) > 0:
                tweet['favorite_count'] = int(cls._extract_attr_value(fav_span[0], 'data-tweet-stat-count'))
            
            # extract hashtags
            hashtags_a = text_p.find_all('a', class_="twitter-hashtag")
            if len(hashtags_a) > 0:
                entities['hashtags'] = [ht.text for ht in hashtags_a]

            # extract symbols
            symbols_a = text_p.find_all('a', class_="twitter-cashtag")
            if len(symbols_a) > 0:
                entities['symbols'] = [s.text for s in symbols_a]
            # extract user_mentions

            # extract urls
            urls_a = text_p.find_all('a', class_="twitter-timeline-link")
            if len(urls_a) > 0:
                for url in urls_a:
                    # excludes hidden urls
                    if('u-hidden' in url.attrs['class']):
                        continue
                    this_url = {
                        'url' : cls._extract_attr_value(url, 'href'),
                        'expanded_url' : cls._extract_attr_value(url, 'data-expanded-url'),
                        'display_url' : None
                    }
                    display_url = url.find('span', class_="js-display-url")
                    if display_url is not None:
                        this_url['display_url'] = display_url.text
                    entities['urls'].append(this_url)

            tweet['entities'] = entities
            tweets.append(tweet)
        return tweets 
    
    def _extract_attr_value(tag, attr):
        if tag.has_attr(attr):
            return tag[attr]
        return None

def t1():
    tw = TwitterWebsiteSearch(0)
    for result in tw.search_generator('$AAPL', '746423373266227200', '693141869211963392'):
        print(result['request'].url)

if __name__ == '__main__':
    # t1()

    tw = TwitterWebsiteSearch(0)
    search_generator = tw.search_generator('$AAPL')

    uniq_tw_ids = {}
    analysis = []
    count = 0

    with open('output.txt', 'w') as f:
        f.write('[')
        for result in search_generator:
            res = {
                'url': result['request'].url, 
                'ids': None,
                'len': None
            }
            ids = []
            for tweet in result['tweets']:
                ids.append(tweet['id_str'])
                count += 1
                # print('{0}, {1}, {2}'.format(count, tweet['id_str'], tweet['text']))
            # print(len(tweets))

            res['ids'] = ids
            res['len'] = len(ids)

            # analysis.append(res)
            # f.write(json.dumps(res, indent=4))
            f.write(json.dumps(result['result'], indent=4))
            f.write(",")
            
            # if count > 100:
            #     break

            # f.write(json.dumps(analysis, indent=4))

        # print(json.dumps(analysis, indent=4))