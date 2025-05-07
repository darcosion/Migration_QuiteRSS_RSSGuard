# Script helping the database migration from QuiteRSS to RSS Guard

The purpose of this repository is to provide the community my homemade script for database migration between my two agregators.
QuiteRSS is a great RSS aggregator, but seem to be currently unmaintained. RSS Guard seems maintained and provides more features that I need.

## What is transferred ? 

Categories, Feeds and News, the news are the longest part because QuiteRSS could have a big history if configured to keep all news.

**If your QuiteRSS is configured to flush old news, please don't use this script, instead export your feeds list in OPML format and import it to RSS Guard, it works better.**

## How to use

This is a simple python3.12 script, you can use the `--help` to see how to specify QuiteRSS and RSS Guard databases : 
```bash
$ python3 insertnews.py --help
Welcom to my news history migration script from QuiteRSS to RSSGuard
usage: insertnews.py [-h] [--quitedb QUITEDB] [--guarddb GUARDDB]

options:
  -h, --help         show this help message and exit
  --quitedb QUITEDB  path for QuiteRSS sqlite database
  --guarddb GUARDDB  path for RSSGuard sqlite database
```

For example, on my context, the command is :  
```bash
python3 insertnews.py --quitedb ~/.local/share/QuiteRss/QuiteRss/feeds.db --guarddb ~/.config/RSS\ Guard\ 4/database/database.db
```
But if you use another OS or another distribution, you should probably adapt path to your context.
