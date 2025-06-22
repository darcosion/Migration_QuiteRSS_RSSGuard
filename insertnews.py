#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil, argparse, sqlite3
from dateutil.parser import parse as catdateparse
import time 

if __name__ == "__main__":
    print("Welcom to my news history migration script from QuiteRSS to RSSGuard")

    parser = argparse.ArgumentParser()
    parser.add_argument("--quitedb", type=str, help="path for QuiteRSS sqlite database")
    parser.add_argument("--guarddb", type=str, help="path for RSSGuard sqlite database")
    args = parser.parse_args()

    #firstly, we backup the database : 
    print("RSS Guard backup")
    shutil.copyfile(args.guarddb, args.guarddb+".quitebackup")

    #here we open the sqlite3 db of RSS Guard
    condest = sqlite3.connect(args.guarddb)

    #here, we read feeds on QuiteRSS sqlite database
    con = sqlite3.connect(args.quitedb)

    # here we ask for the account_id
    account_id = None
    account_ids = condest.execute("SELECT count(id) FROM Accounts WHERE type IS 'std-rss'").fetchone()[0]
    if(account_ids > 1):
        print("multiple 'std-rss' account, please put the std-rss account id you want bellow")
        account_ids = condest.execute("SELECT id, custom_data FROM Accounts WHERE type IS 'std-rss'")
        for i in account_ids:
           print(i)
        account_id = int(input("write here the number corresponding to your std-rss"))
    else:
        account_id = condest.execute("SELECT id FROM Accounts WHERE type IS 'std-rss'").fetchone()[0]

    ## firstly, we will import feeds from QuiteRSS and convert them to categories and feeds

    #we start by extracting categories : 
    print("copy categories")
    categoriesrows = con.execute("SELECT id, text, title, parentId FROM feeds WHERE xmlUrl IS NULL")
    ordrdict = dict()
    for row in categoriesrows:
        if(row[3] not in ordrdict.keys()):
            ordrdict[row[3]] = 0
        else:
            ordrdict[row[3]] += 1
        try:
            querytext = """INSERT INTO "Categories"
                        ("id", "parent_id", "title", "description", "account_id", "ordr")
                        VALUES (?, ?, ?, ?, ?, ?);"""
            if(int(row[3]) == 0):
                condest.execute(querytext, (row[0], -1, row[1], row[2], account_id, ordrdict[row[3]]))
            else:
                condest.execute(querytext, (row[0], row[3], row[1], row[2], account_id, ordrdict[row[3]]))
            
        except Exception as e:
            print(e)
            exit()
    
    print(ordrdict)
    # we continue by extracting feeds
    print("copy feeds")
    feedsrows = con.execute("SELECT id, text, title, parentId, xmlUrl, disableUpdate FROM feeds WHERE xmlUrl IS NOT NULL")
    for row in feedsrows:
        if(row[3] not in ordrdict.keys()):
            ordrdict[row[3]] = 0
        else:
            ordrdict[row[3]] += 1
        try:
            querytext = """INSERT INTO "main"."Feeds"
                            ("id", "ordr", "title", "description", "category", "source", "update_type", "is_off", "account_id", "custom_id")
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
            if(int(row[3]) == 0):
                condest.execute(querytext, (row[0], ordrdict[row[3]], row[1], row[2], -1, row[4], 1, row[5], account_id, row[0]))
            else:
                condest.execute(querytext, (row[0], ordrdict[row[3]], row[1], row[2], row[3], row[4], 1, row[5], account_id, row[0]))
            
        except Exception as e:
            print(e)
            exit()
    print(ordrdict)

    condest.commit()
    ## secondly we gather how many query we need to do : 
    countrows = con.execute("select count(id) from news;")
    countrows = countrows.fetchone()[0] 
    steprows = 0
    rows = None

    # we loop until we have the whole news database
    print("copy news")
    while(steprows < countrows):
        rowsquery = "SELECT feedId, title, link_href, author_name, description, published, deleted, guid FROM news LIMIT 500 OFFSET {};".format(steprows)
        print(rowsquery)
        rows = con.execute(rowsquery)
        for row in rows:
            # here, we inject QuiteRSS news on RSS Guard Messages

            # first if the article is deleted, we don't insert it
            if(int(row[6]) == 1):
                #print("row {} with title {} deleted, so not imported".format(row[0], row[1]))
                continue
            
            # else, we try to insert the article
            try:
                #here, we convert timestamp
                timestamp = catdateparse(row[5])
                if timestamp.year <= 1971:  
                    timestamp = time.time()
                else:
                    timestamp = timestamp.timestamp()*1000
                querytext = """INSERT INTO Messages 
                    ("is_read", "is_important", "is_deleted", "is_pdeleted", 
                    "feed", 
                    "title", 
                    "url", 
                    "author", 
                    "date_created", 
                    "contents", 
                    "enclosures", 
                    "score", 
                    "account_id", 
                    "custom_id", 
                    "custom_hash", 
                    "labels") VALUES (
                    1, 
                    0, 
                    0, 
                    0, 
                    ?, 
                    ?, 
                    ?, 
                    ?, 
                    ?,
                    ?, 
                    '[]', 
                    0, 
                    ?, 
                    ?, 
                    '', 
                    '.')"""
                if(row[1] == ''):
                    condest.execute(querytext, (row[0], "no title", row[2], row[3], timestamp, row[4], account_id, row[7]))
                else:
                    condest.execute(querytext, (row[0], row[1], row[2], row[3], timestamp, row[4], account_id, row[7]))

            except Exception as e:
                print(e)
                print(querytext)
                print((row[0], row[1], row[2], row[3], timestamp, row[4], account_id, row[7]))
                exit()
            
        steprows += 500
    
    print("end of insert, start commiting")
    condest.commit()
    print("end of commit, closing database connexion")
    con.close()
    condest.close()
    
else:
    print("this is a CLI tool, please use it on a proper shell")
