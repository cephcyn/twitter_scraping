## Twitter Scraper

Twitter makes it hard to get all of a user's tweets (assuming they have more than 3200). This is a way to get around that using Python, Selenium, and Tweepy.

Essentially, we will use Selenium to open up a browser and automatically visit Twitter's search page, searching for a single user's tweets on a single day. If we want all tweets from 2015, we will check all 365 days / pages. This would be a nightmare to do manually, so the `scrape.py` script does it all for you - all you have to do is input a date range and a twitter user handle, and wait for it to finish.

The `scrape.py` script collects tweet ids. If you know a tweet's id number, you can get all the information available about that tweet using Tweepy - text, timestamp, number of retweets / replies / favorites, geolocation, etc. Tweepy uses Twitter's API, so you will need to get API keys. Once you have them, you can run the `get_metadata.py` script.

## Requirements

- basic knowledge on how to use a terminal
- Safari 10+ with 'Allow Remote Automation' option enabled in Safari's Develop menu to control Safari via WebDriver.
- conda (miniconda or anaconda)
  - to check: in your terminal, enter `conda`
  - if you don't have it, check online for installation instructions

## Running the scraper

- first you'll need to get twitter API keys
  - sign up for a developer account here: [https://dev.twitter.com/](https://dev.twitter.com/)
  - get your keys here: [https://apps.twitter.com/](https://apps.twitter.com/)
- put your twitter API keys into a place where the scripts can use them
  - make a copy of the `sample_api_keys.json` file named `api_keys.json`
    - `cp sample_api_keys.json api_keys.json`
  - put your twitter API keys into the new `api_keys.json` file
- set up your python (conda) environment
  - install the `twitter_scraping` conda environment from `environment.yml`
    - `conda env create -f environment.yml`
- tell the script which settings to use while scraping
  - open up `scrape.py` and edit the user, start, and end variables (and save the file)
- run `./run.sh`
  - you may see some output in the terminal
  - you may also see a browser pop up, don't close it!
- do some fun other task until it finishes!
- once it's done, it outputs all the tweet ids it found into `all_ids.json`
- every time you run the scraper with different dates, it will add the new ids to the same file
  - it automatically removes duplicates so don't worry about small date overlaps

## Troubleshooting the scraper

- do you get a `no such file` error? you need to cd to the directory of `scrape.py`
- do you get a driver error when you try and run the script?
  - open `scrape.py` and change the driver to use Chrome() or Firefox()
    - if neither work, google the error (you probably need to install a new driver)
- does it seem like it's not collecting tweets for days that have tweets?
  - open `scrape.py` and change the delay variable to 2 or 3 (or more)

## Getting the metadata

- open up `get_metadata.py` and edit the user variable (and save the file)
- run `python3 get_metadata.py`
- this will get metadata for every tweet id in `all_ids.json`
- it will create 4 files
  - `username.json` (master file with all metadata)
  - `username.zip` (a zipped file of the master file with all metadata)
  - `username_short.json` (smaller master file with relevant metadata fields)
  - `username.csv` (csv version of the smaller master file)
