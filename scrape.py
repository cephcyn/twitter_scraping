import csv
import datetime
import glob
import json
import math
import os.path
import pickle
import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import sys
from time import sleep
import tweepy
from tweepy import TweepError
import zipfile
import zlib

date_mapping = {}

def getIdsByAdvSearch(api, user):
    """
    Given a username, writes a files to ./ids containing IDS for every tweet they have made.
    """
    userdata = api.get_user(user)
    # print to log some information about the user
    print(f'now adv-searching user:{user}', flush=True)
    print(f'{user} created {str(userdata.created_at)}', flush=True)
    print(f'{user} has {str(userdata.statuses_count)} statuses total', flush=True)

    # search date interval set-up
    # start searching from the account creation date (inclusive)
    start = datetime.datetime.strptime(
        str(userdata.created_at), "%Y-%m-%d %H:%M:%S")  # year, month, day.
    # ... unless we have evidence that this account has been scraped before
    # then start from the last scraped date
    if user in date_mapping:
        start = date_mapping[user]
    # settings: date to search starting from (uncomment below to set manual date, otherwise defaults to account creation or last scraped data)
    # start = datatime.datetime(2019, 1, 1)
    # settings: date to search until (EXCLUSIVE: this one is important)
    end = datetime.datetime(2020, 1, 1)

    # webdriver and load delay set-up
    # settings: number of seconds to wait between each manual webdriver search
    delay = 10
    # settings: number of seconds to wait between each scroll action
    scroll_delay = 1
    # set up headless browser - so it doesn't open up a browser window
    opts = webdriver.FirefoxOptions()
    opts.headless = True
    # settings: which browser to use (defaults to Firefox)
    driver = webdriver.Firefox(options=opts)  # options are Chrome(), Firefox(), Safari()

    # search interval set-up
    # settings: number of days to include in each interval
    day_interval = 1

    # do NOT change the below.
    twitter_ids_filename = f'ids/all_ids_{user}.json'  # file to write to
    # updated to match Twitter format as of 2020/10/05
    tweet_selector = "div[data-testid='tweet']"
    id_selector = "a[dir='auto'][role='link'][data-focusable='true']"
    ids = []

    def format_day(date):
        """
        Given a date, creates a string representing that date usable for adv search
        """
        day = '0' + str(date.day) if len(str(date.day)) == 1 else str(date.day)
        month = '0' + str(date.month) if len(str(date.month)) == 1 else str(date.month)
        year = str(date.year)
        return '-'.join([year, month, day])

    def form_url(since, until):
        """
        Given the start and end dates, returns the URL for advanced searching on this user for this interval.
        """
        # return the direct feed link??
        # return ('https://twitter.com/' + user)
        p1 = 'https://twitter.com/search?f=tweets&vertical=default&q=from%3A'
        p2 = user + '%20since%3A' + since + '%20until%3A' + \
            until + '%20include%3Aretweets%20include%3Anativeretweets&src=typd'
        return p1 + p2

    def increment_day(date, i):
        """
        Add to the date by i days.
        """
        return date + datetime.timedelta(days=i)

    try:
        # settings: the cutoff for manual scrolling (defaults to 2900, Twitter API says up to 3200 should be safe)
        manual_scrolling_cutoff = 2900
        if int(userdata.statuses_count) < cutoff_manual_scrolling:
            # scrape by using the API.
            print("scraping with API")
            for status in tweepy.Cursor(api.user_timeline, screen_name=user, tweet_mode="extended").items():
                ids.append(status.id)
            # Print number of tweets found
            print(f'{len(ids)} tweets found, {len(ids)} total', flush=True)
        else:
            # Scrape by searching repeatedly with a URL.
            print("scraping with URL search")
            while min([start, end]) != end: # for i in range(int(num_intervals)):
                # Generate URL to search with
                d1 = format_day(increment_day(start, 0))
                d2 = format_day(min([increment_day(start, day_interval), end])) # don't exceed end date
                url = form_url(d1, d2)
                print(f'{d1} to {d2} /// on URL: {url}')
                date_mapping[user] = start # assume we've scraped thoroughly up to the point of d1
                driver.get(url)
                sleep(delay)
                # Grab tweets
                try:
                    # scroll to bottom of page until we can't scroll any more
                    lenOfPage = driver.execute_script(
                        'window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;')
                    match = False
                    while (match == False):
                        lastCount = lenOfPage
                        sleep(scroll_delay)
                        lenOfPage = driver.execute_script(
                            'window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;')
                        if lastCount == lenOfPage:
                            match = True
                    # Get tweets
                    found_tweets = driver.find_elements_by_css_selector(
                        tweet_selector)
                    # Print number of tweets found
                    print(f'{len(found_tweets)} tweets (from any user) found, {len(ids)} total', flush=True)
                    # Write the tweets that we found into "ids" output file
                    for tweet in found_tweets:
                        try:
                            id_href = tweet.find_element_by_css_selector(
                                id_selector).get_attribute('href').split('/')
                            if id_href[-3].lower() == user.lower():
                                ids.append(id_href[-1])
                        except StaleElementReferenceException as e:
                            print(f'lost element reference {tweet}')
                except NoSuchElementException:
                    print('no tweets on this day')
                # Move on to the next interval...
                start = increment_day(start, day_interval)
                # and checkpoint the date mappings...
                pickle.dump(date_mapping, open(f'date_mapping.pickle', 'wb'))
    finally:
        # Write collected IDs to file...
        prev_ids = []
        if os.path.isfile(twitter_ids_filename):
            with open(twitter_ids_filename, 'r') as f:
                print(f'appending ids to those already in file for {user}')
                prev_ids = json.load(f)
                print(f'previously had {len(prev_ids)} tweets in file for {user}')
        with open(twitter_ids_filename, 'w') as f:
            all_ids = list(set(ids + prev_ids))
            print(f'tweets found on this scrape: {len(ids)}')
            print(f'total tweet count: {len(all_ids)}', flush=True)
            json.dump(all_ids, f)
        # Clean up
        print(f'all done for {user}', flush=True)
        driver.close()


def readTweets(api, user):
    """
    Given a username (and assuming the appropriate file in ./ids exists for that user),
    writes all tweets listed in ./ids for that user into files in ./data
    """
    output_file = f'data/{user}.json'
    output_file_short = f'data/{user}_short.json'
    compression = zipfile.ZIP_DEFLATED

    with open(f'ids/all_ids_{user}.json') as f:
        ids = json.load(f)

    print(f'total ids: {len(ids)}')

    all_data = []
    start = 0
    end = 100
    limit = len(ids)
    i = math.ceil(limit / 100)

    for go in range(i):
        print(f'currently getting {start} - {end}')
        sleep(6)  # needed to prevent hitting API rate limit
        id_batch = ids[start:end]
        start += 100
        end += 100
        tweets = api.statuses_lookup(id_batch)
        for tweet in tweets:
            all_data.append(dict(tweet._json))

    print('metadata collection complete')
    print('creating master json file', flush=True)
    with open(output_file, 'w') as outfile:
        json.dump(all_data, outfile)

    print('creating zipped master json file', flush=True)
    zf = zipfile.ZipFile(f'data/{user}.zip', mode='w')
    zf.write(output_file, compress_type=compression)
    zf.close()

    results = []

    def is_retweet(entry):
        return 'retweeted_status' in entry.keys()

    def get_source(entry):
        if '<' in entry["source"]:
            return entry["source"].split('>')[1].split('<')[0]
        else:
            return entry["source"]

    with open(output_file) as json_data:
        data = json.load(json_data)
        for entry in data:
            # settings: "relevant" tweet metadata (please reconfig this carefully...)
            t = {
                "created_at": entry["created_at"],
                "text": entry["text"],
                "in_reply_to_screen_name": entry["in_reply_to_screen_name"],
                "retweet_count": entry["retweet_count"],
                "favorite_count": entry["favorite_count"],
                "source": get_source(entry),
                "id_str": entry["id_str"],
                "is_retweet": is_retweet(entry)
            }
            results.append(t)

    print('creating minimized json master file', flush=True)
    with open(output_file_short, 'w') as outfile:
        json.dump(results, outfile)

    with open(output_file_short) as master_file:
        data = json.load(master_file)
        # settings: "relevant" tweet metadata field names. (CHANGE THIS TOGETHER WITH OTHER RELEVANT DATA SETTINGS)
        fields = ["favorite_count", "source", "text", "in_reply_to_screen_name",
                  "is_retweet", "created_at", "retweet_count", "id_str",
                  "date_collected"]
        print('creating CSV version of minimized json master file', flush=True)
        print()
        f = csv.writer(open(f'data/{user}.csv', 'w'))
        f.writerow(fields)
        for x in data:
            f.writerow([x["favorite_count"], x["source"], x["text"], x["in_reply_to_screen_name"],
                        x["is_retweet"], x["created_at"], x["retweet_count"], x["id_str"],
                        datetime.date.today()])


def main(usersToScrape):
    """
    Given a list of strings representing all usernames to scrape Tweets from,
    writes files to ./ids and ./data representing all tweets written by those users.
    """
    with open('api_keys.json') as f:
        keys = json.load(f)

    auth = tweepy.OAuthHandler(keys['consumer_key'], keys['consumer_secret'])
    auth.set_access_token(keys['access_token'], keys['access_token_secret'])
    api = tweepy.API(auth)
    for user in usersToScrape:
        # print(f'CURRENTLY TRYING :{user}:', flush=True)
        try:
            # if a checkpoint already exists, restore from there and continue
            if os.path.isfile(f'ids/all_ids_{user}.json'):
                # first check to see if the count is within accuracy margin
                # settings: percentage error margin for tweet count accuracy (not sure how accurate twitter API is)
                # this parameter exists because sometimes the twitter API reports more tweets than actually exist
                # sometimes the users delete tweets, and/or you don't actually need to grab ALL of the user's history of tweets.
                # This is the accuracy margin we want to have to decide that we've got all the tweets.
                # Set it to 0 if you want to get the exact number of tweet IDs that Twitter says a user has created.
                # Set it to 0.05 if you want to get within 5% of that number.
                # Set it to 1 or above 1 if you want re-scraping to never happen.
                accuracy_margin = 0.00
                # assume the ID file exists if the data file exists...
                # get collected number of tweets
                with open(f'ids/all_ids_{user}.json') as f:
                    ids = json.load(f)
                # get expected number of tweets
                userdata = api.get_user(user)
                statuses_count = int(userdata.statuses_count)
                # check if we actually need to re-scrape this account:
                # if it has tweets and the number we already got is outside margin
                if statuses_count > 0 and \
                        abs(len(ids) - statuses_count) / statuses_count > accuracy_margin:
                    print(f'{user} is not done: got {len(ids)} / {statuses_count} tweets', flush=True)
                    getIdsByAdvSearch(api, user)
                    readTweets(api, user)
                    with open(f'ids/all_ids_{user}.json') as f:
                        ids_new = json.load(f)
                    # print(f'{user} updated # tweets from {len(ids)} to {len(ids_new)} / {statuses_count} tweets', flush=True)
                else:
                    print(f'{user} is done: got {len(ids)} / {statuses_count} tweets', flush=True)
            else:
                # if there is no previous checkpoint, scrape as new
                getIdsByAdvSearch(api, user)
                readTweets(api, user)
        except selenium.common.exceptions.WebDriverException as e:
            print(f'exception thrown on {user}, re-trying', flush=True)
            print(e)
            usersToScrape.append(user)
        except tweepy.error.TweepError as e:
            print(f'tweepy error on {user}, not re-trying', flush=True)
            print(e)
            print()
        except FileNotFoundError as e:
            print(f'file for {user} not found, not re-trying', flush=True)
            print(e)
            print()


if __name__ == "__main__":
    # load previous saved scrape dates if it exists
    if os.path.isfile(f'date_mapping.pickle'):
        date_mapping = pickle.load(open(f'date_mapping.pickle', 'rb'))
    input = csv.DictReader(open('input.csv'))
    handles_to_ids = {}
    # build up collection of usernames to search
    for row in input:
        handles_to_ids[row['twitter_handle']] = row['meta_id_number']
    # write the data files containing tweets for each of these accounts
    main(handles_to_ids.keys())
    # write the merged data file containing firm ID, twitter handle, and tweets
    field_names = [
        'meta_id_number',
        'twitter_handle',
        'created_at',
        'text',
        'in_reply_to_screen_name',
        'retweet_count',
        'favorite_count',
        'source',
        'is_retweet',
        'id_str',
        'date_collected',
    ]
    output = csv.DictWriter(open('merged_data.csv', 'w'), fieldnames=field_names)
    output.writeheader()
    for handle in handles_to_ids.keys():
        try:
            handle_tweets = csv.DictReader(open(f'data/{handle}.csv'))
            for row in handle_tweets:
                # add fields not scraped with the tweet itself
                # settings: add any extra fields wanted in the output here (please reconfig this carefully...)
                row['meta_id_number'] = handles_to_ids[handle]
                row['twitter_handle'] = f'{handle}'
                output.writerow(row)
        except Exception as e:
            print(f'error occurred on {handle} while merging data:')
            print(e)
            print(flush=True)

