# HOW THE SCRIPT WORKS

- For each account listed in `input.csv`, it grabs all the tweets.
- I do one of two things for each account:
  - If reported # of tweets is below the Twitter API limit (anecdotally this is around 3200, but I use 2900 as cutoff):
    - Grab all of the tweets using the Twitter API. This includes retweets, replies, etc.
  - If # of tweets is above the API limit:
    - Grab all of the tweets by opening up Firefox browser and manually scrolling through their history.
    - There are some settings in the Python file that control how this scraping is done:
      - Date ranges to get tweets within
      - Pagination (how much of a range to grab per page)
      - How long to wait before scrolling down / performing a new search.
        - This can be adjusted if the computer you're running the script on is extra slow or something.
    - These settings are relatively self-documenting within the file. Just change the number.
      - You can find these sections by searching for "settings" in the python file
    - Note that this method of searching manually actually excludes certain types of retweets because of flaws in Twitter's advanced search. I'm not sure what tweets exactly are not included, or why they are(n't) included, but I have some ideas...
      - Includes: retweets that add content
      - Includes: discussion replies
      - Excludes: retweets that don't add any content. I.e. just a photo from another account, no extra words added
- The script also includes a checkpointing system in case of a crash or if you need to interrupt it.
  - If interrupted, it will dump all current IDs it has found to the output JSON files and stop running.
  - If you start it up again, it will load any already-existing JSON files, check if it already got all tweets, and continue scraping from there if necessary.
- When I have a list of IDs for each tweet (a bunch of files saved into `./ids` folder), I get the data for each tweet.
  - This code is directly taken from the original Twitter scraping code. Minimally adapted
  - The data for the tweets is output into four files per Twitter handle: `[username].csv`, `[username].json`, `[username].zip`, and a `[username]_short.json` file
  - I also merge all of this data together into a single file `merged_data.csv` that can easily be converted into a large Excel/xlsx sheet, or imported into something else

# THE FORMAT OF THE OUTPUT FILE `merged_data.csv`

- Each row represents a single Tweet.
- The columns of the output CSV:
  - `meta_id_number` : The number mapped to the account handle in `input.csv`.
  - `twitter_handle` : The handle/username of the Twitter account
  - `created_at` : Timestamp (in UTC, +0000) that the tweet was created. Data directly from Twitter.
  - `text` : The text of the tweet. Data directly from Twitter.
  - `in_reply_to_screen_name` : If the tweet was a reply to someone, then their username. Otherwise blank. Data directly from Twitter.
  - `retweet_count` : Number of retweets on the tweet as of the `date_collected`. Data directly from Twitter.
  - `favorite_count` : The number of likes (favorites) on the tweet as of the `date_collected`. Data directly from Twitter.
  - `source` : The device that was used to send the tweet. Data directly from Twitter.
  - `is_retweet` : If the tweet is a retweet of something else. Data directly from Twitter.
  - `id_str` : The 18-digit unique ID number of the tweet. Data directly from Twitter.
  - `date_collected` : The date that metadata was collected about the tweets.

# THE FORMAT OF THE INPUT FILE `input.csv`

- Maps from some meta ID value to Twitter handles
- The value of the meta ID value is intended to help organize data or index the provided handles, it has no impact on the data collection itself

# OTHER NOTES / TODOS?

- There can be a substantial number of tweets missing from prolific accounts
- A possible explanation is that they've deleted a large fraction of all tweets made (typos, redacted, other reasons?)
  - Another possible explanation is that a lot of the tweets "missing" were made after the scraping cutoff date (marked as a setting in the scraping script)
  - Finally, it's possible the script was blocked from scraping them (see below), even though I was careful to avoid rate limiting.
- Sometimes Twitter temporarily blocks IPs from running advanced searches.
  - I ran into this issue earlier, when the code was still doing the manual/advanced searches for every single user.
  - You can notice this issue if advanced searches are not returning any results and you are getting empty output files, despite the account clearly having original tweets.
  - I don't know what way there is to solve it other than waiting out the temporary block or increasing the wait delay (see settings)
  - Maybe try running it on a different computer on a different network?
- Raw (non-text-added) retweets are oddly handled.
  - I have not figured out an elegant way to include these.
  - The Twitter search system itself is flawed in that it does not fully support these.
  - Furthermore, the API does not offer a way to retrieve these fully.
  - As some context: Twitter has changed how retweets and replies are implemented several time over its history, so there's several different "official" response types that users have used in the past.

