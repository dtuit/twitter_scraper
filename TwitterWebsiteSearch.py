import requests
from requests import Request, Session
from datetime import datetime, timezone
from time import sleep
import lxml
import lxml.html as lh
from urllib.parse import quote, urlsplit
import re
from operator import itemgetter

base_url = 'https://twitter.com/i/search/timeline'

def search(query, min_tweet_id=None, max_tweet_id=None, aditional_params=None, session=None):
    """
    
    """
    # Init query parameters
    params = {'q' : quote(query)}
    if aditional_params is not None:
        params = aditional_params
        params['q'] = quote(query)        

    # Create Request
    if min_tweet_id is not None and max_tweet_id is not None:
        params['max_position'] = encode_max_postion_param(min_tweet_id, max_tweet_id)
    request = prepare_request(params)

    # Execute Request
    result = execute_request(request, session)
    result_json = result.json()

    # Extract Results
    tweets = []
    if result_json is not None and result_json['items_html'] is not None:
        tweets = parse_tweets(result_json['items_html']) 

    # Return Result
    return {
        '_request': request,
        '_result': result,
        '_result_json': result_json,
        'tweets': tweets
        }

def prepare_request(params):
    payload_str = "&".join("%s=%s" % (k,v) for k,v in params.items())
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/29.0.1547.65 Chrome/29.0.1547.65 Safari/537.36',
        'Accept-Encoding' : 'gzip, deflate, sdch, br'
        }
    cookie = {}
    req = Request('GET', base_url, params=payload_str, headers=headers, cookies=cookie)
    return req.prepare()

def execute_request(prepared_request, session=None):
    try:
        if session is None:
            session = Session()
        result = session.send(prepared_request)
        # print(prepared_request.url)
        return result
    except requests.exceptions.Timeout as e:
        raise

def _parse_tweet(tweetElement):
    li = tweetElement
    tweet = {
        'created_at' : None,
        'id_str' : li.get('data-item-id'),
        'text' : None,
        'lang' : None,
        'entities': {
            'hashtags': [],
            'symbols':[],
            'user_mentions':[],
            'urls':[],
        },
        'user' : {
            'id_str' : None, 
            'name' : None,
            'screen_name': None,
            'profile_image_url': None,
            'verified': False
            },
        'retweet_count' : 0,
        'favorite_count' : 0,
        'is_quote_status' : False,
        'in_reply_to_user_id': None,
        'in_reply_to_screen_name' : None,
        'contains_photo': False,
        'contains_video': False,
        'contains_card': False
        
    }   

    content_div = li.cssselect('div.tweet')
    if len(content_div) > 0:
        content_div = content_div[0]
        tweet['user']['id_str'] = content_div.get('data-user-id')
        tweet['user']['name'] = content_div.get('data-name')
        tweet['user']['screen_name'] = content_div.get('data-screen-name')
    
    reply_a = content_div.cssselect('div.tweet-context a.js-user-profile-link')
    if len(reply_a) > 0:
        tweet['in_reply_to_user_id'] = reply_a[0].get('data-user-id')
        tweet['in_reply_to_screen_name'] = reply_a[0].get('href') # remove /

    user_img = content_div.cssselect('img.avatar')
    if len(user_img) > 0:
        tweet['user']['profile_image_url'] = user_img[0].get('src')
    
    text_p = content_div.cssselect('p.tweet-text')
    if len(text_p) > 0:
        text_p = text_p[0]
        tweet['text'] = text_p.text_content()
        tweet['lang'] = text_p.get('lang')
    
    verified_span = content_div.cssselect('span.Icon--verified')
    if len(verified_span) > 0:
        tweet['user']['verified'] = True
    
    date_span = content_div.cssselect('span._timestamp')
    if len(date_span) > 0:
        tweet['created_at'] = datetime.fromtimestamp(int(date_span[0].get('data-time-ms'))/1000, timezone.utc).strftime('%Y-%m-%d %H:%M:%S%z') 
    
    counts = li.cssselect('span.ProfileTweet-action--retweet, span.ProfileTweet-action--favorite')
    if len(counts) > 0:
        for c in counts:
            classes = c.get('class').split(' ')
            if 'ProfileTweet-action--retweet' in classes:
                tweet['retweet_count'] = c[0].get('data-tweet-stat-count')
            elif 'ProfileTweet-action--favorite' in classes:
                tweet['favorite_count'] = c[0].get('data-tweet-stat-count')

    entities = tweet['entities']
    _parse_tweet_entites(text_p, entities)

    quoted_tweet_context = content_div.cssselect('div.QuoteTweet-innerContainer')
    if len(quoted_tweet_context) > 0:
        quoted_tweet_context = quoted_tweet_context[0]
        tweet['is_quote_status'] = True
        tweet['quoted_status_id_str'] = quoted_tweet_context.get('data-item-id')
        tweet['quoted_status'] = {
                'id_str': None,
                'text': None,
                'user': {
                    'id_str' : None,
                    'name' : None,
                    'screen_name' : None,
                },
                'entities' : {
                    'hashtags' : [],
                    'symbols' :[],
                    'user_mentions':[],
                    'urls':[]
                }
            }
        qtweet = tweet['quoted_status']

        qtweet['id_str'] = quoted_tweet_context.get('data-item-id')
        qtweet['user']['id_str'] = quoted_tweet_context.get('data-user-id')
        qtweet['user']['screen_name'] = quoted_tweet_context.get('data-screen-name')

        qt_user_name = quoted_tweet_context.cssselect('b.QuoteTweet-fullname')
        if len(qt_user_name) > 0:
            qtweet['user']['name'] = qt_user_name[0].text_content()
        
        qt_text = quoted_tweet_context.cssselect('div.QuoteTweet-text.tweet-text')
        if len(qt_text) > 0:
            qt_text = qt_text[0]
            qtweet['text'] = qt_text.text_content()

        qt_entites = qtweet['entities']
        _parse_tweet_entites(qt_text, qt_entites)
    
    tweet_media_context = content_div.cssselect('div.AdaptiveMedia-container')
    if len(tweet_media_context) > 0:
        tweet_media_context = tweet_media_context[0]
        tweet['entities']['media'] = []
        photo_found = False
        tweet_media_photos = tweet_media_context.cssselect('div.AdaptiveMedia-photoContainer')
        for elm in tweet_media_photos:
            tweet['contains_photo'] = photo_found = True
            photo = {
               'media_url' : elm.get('data-image-url'),
               'type' : 'photo'
            }
            tweet['entities']['media'].append(photo)
        if not photo_found:
            tweet_media_video = tweet_media_context.cssselect('div.AdaptiveMedia-videoContainer')
            if len(tweet_media_video) > 0:
                tweet['contains_video'] = True
                video = {
                    'type' : 'video',
                    'video_type' : re.search(re.compile(r"PlayableMedia--([a-zA-Z]*)"), tweet_media_video[0].cssselect('div[class*="PlayableMedia--"]')[0].get('class')).group(1),
                    'media_url' : 'https://twitter.com/i/videos/tweet/' + tweet['id_str'],
                    'video_thumbnail' : re.search(re.compile(r"background-image:url\(\'(.*)\'"),tweet_media_video[0].cssselect('div.PlayableMedia-player')[0].get('style')).group(1)
                }
                tweet['entities']['media'].append(video)
        # print(tweet['entities']['media'])

    else:
        tweet_media_context = content_div.cssselect('div.card2')
        if len(tweet_media_context) > 0:
            pass




    return tweet

def _parse_tweet_entites(element, entities):
    tags = element.cssselect('a.twitter-hashtag, a.twitter-cashtag, a.twitter-atreply, a.twitter-timeline-link')
    if len(tags) > 0:
        for tag in tags:
            classes = tag.get('class').split(' ')
            if 'twitter-hashtag'in classes:
                entities['hashtags'].append(tag.text_content()) #remove # symbol
            elif 'twitter-cashtag' in classes:
                entities['symbols'].append(tag.text_content()) #remove $ symbol
            elif 'twitter-atreply' in classes:
                mentioned_user = {
                    'id_str' : tag.get('data-mentioned-user-id'),
                    'screen_name' : tag.text_content() #remove @ symbol
                }
                entities['user_mentions'].append(mentioned_user)
            elif 'twitter-timeline-link' in classes: # and 'u-hidden' not in classes
                url = {
                    'url': tag.get('href'),
                    'expanded_url' : tag.get('data-expanded-url'),
                    'display_url' : None
                }
                display_url = tag.cssselect('span.js-display-url')
                if len(display_url) > 0:
                    url['display_url'] = display_url[0].text_content()
                entities['urls'].append(url)

def _parse_tweet_media(element, media):
    pass


def parse_tweets(items_html):
    try:
        html = lh.fromstring(items_html)
    except lxml.etree.ParserError as e:
        return []
    tweets = []
    for li in html.cssselect('li.js-stream-item'):
        
        # Check if is a tweet type element
        if 'data-item-id' not in li.attrib:
            continue
        tweet = _parse_tweet(li)
        tweets.append(tweet)

    return tweets

def encode_max_postion_param(min, max):
    return "TWEET-{0}-{1}".format(min, max)

class TwitterPager():
    def __init__(self, 
                rate_delay=0,
                error_delay=5,
                timeout=5,
                retry_limit=4,
                continue_on_empty_result=True,
                session=Session()):
        self.rate_delay = rate_delay
        self.error_delay = error_delay
        self.timeout = timeout
        self.retry_limit = retry_limit
        self.continue_on_empty_result = continue_on_empty_result
        self.session = session

    def execute_request(prepared_request, session=None):
        try:
            return execute_request(prepared_request, session)
        except requests.exceptions.Timeout as e:
            print(e.message)
            print("Sleeping for {:d}".format(self.error_delay))
            sleep(self.error_delay)
            return self.execute_request(prepared_request)

    def get_iterator(self, query, min_tweet_id=None, max_tweet_id=None, aditional_params=None):
        result = search(query, min_tweet_id, max_tweet_id, aditional_params)
        prev_min_tweet_id = None
        yield result

        while True:

            if len(result['tweets']) == 0:
                if not self.continue_on_empty_result:
                    print('No tweets returned terminating program')
                    break
                else:
                    # Sometimes the API stops returning tweets even when there are more
                    # we can try to find these tweets by modifying the max_position parameter.
                    int_min_id = int(min_tweet_id)
                    for x in range(8, len(min_tweet_id)): #TODO impl something more sophisticated 
                        min_to_try = int_min_id - 10**x
                        result = search(query, str(min_to_try), max_tweet_id, aditional_params)
                        if len(result['tweets']) > 0:
                            break
                    else:
                        print('No tweets returned terminating program')
                        # if we didnt find any point to continue from, break.
                        break

            if max_tweet_id is None:
                max_tweet_id = result['tweets'][0]['id_str']
            
            # In a high volume search query like 'a' must use the max_tweet_id provided by the result,
            # otherwise the same results will be returned many times. (only happens during the first ~10 pages of results)
            res_min_pos = result['_result_json'].get('min_position')
            if res_min_pos is not None:
                split = res_min_pos.split('-')
                max_tweet_id = split[2]

            prev_min_tweet_id = min_tweet_id
            min_tweet_id = result['tweets'][-1]['id_str']

            # If the current request returns the same tweets as the last
            # the query is configured wrong
            # TODO create more accurate metric
            if prev_min_tweet_id is min_tweet_id:
                break

            result = search(query, min_tweet_id, max_tweet_id, aditional_params, self.session)
            
            yield result

def inorder(tweets):
    tweets_sorted = sorted(tweets, key=itemgetter('id_str')) 

if __name__ == '__main__':
    with open('output.txt', 'w') as f:
        f.close()
    import json
    count = 0
    for x in TwitterPager().get_iterator('a'):
        with open('output.txt', 'a') as f:
            reses = []
            for t in x['tweets']:
                reses.append(t['id_str'])
                # reses.append([t['id_str'], t['created_at']])
            print("{} {} {} {}".format(count, len(x['tweets']), x['_request'].url, x['_result_json'].get('min_position')))
            f.write(json.dumps(reses, indent=4))
            # f.write(json.dumps(x['tweets'], indent=4))
            count += 1

            if count == 5:
                break