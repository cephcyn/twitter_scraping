#!/usr/bin/env bash

# activate conda environment
conda activate twitter_scraping

# add geckodriver to path
export PATH="./:$PATH"

# run the scraper script
python3 scrape.py

