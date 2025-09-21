#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil, argparse, sqlite3
from datetime import datetime, timezone, timedelta


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
    
    
    # news from QuiteRSS: feedId, title, link_href, guid, description, published, author_name, read, starred, deleted

    # Messages from RSSGuard: feed, title, url, custom_id, contents, date_created (timestamp), author, is_read, is_important, is_deleted, is_pdeleted
    
    # read = 0 --> is_read == 0
    # read = 2 --> is_read == 1
    # starred = 0 --> is_important = 0
    # starred = 1 --> is_important = 1
    # deleted = 0 --> is_deleted = 0
    # deleted = 1 --> is_pdeleted = 1
    # deleted = 2 --> is_deleted = 1


    # Connect to the first SQLite database
    cursor1 = con.cursor()
    
    # Connect to the second SQLite database
    cursor2 = condest.cursor()
    
    # Define the SELECT query to retrieve the desired columns from the first table
    select_query = """
    SELECT feedId, title, link_href, guid, description, published, author_name, read, starred, deleted
    FROM news
    """
    
    # Execute the SELECT query
    cursor1.execute(select_query)
    rows = cursor1.fetchall()
    
   
    # Define the INSERT query to insert the retrieved data into the second table
    insert_query = """
    INSERT INTO Messages (is_read, is_important, is_deleted, is_pdeleted, feed, title, url, author, date_created, contents, enclosures, score, account_id, custom_id, custom_hash, labels )

    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    # Specify your desired timezone offset
    timezone_offset = 0  # Replace with your desired offset in hours
    desired_timezone = timezone(timedelta(hours=timezone_offset))
        
    # Transform the published column values to UNIX timestamps and create a list of tuples
    transformed_rows = [
        (
            1 if row[7] == 2 else 1 if row[9] == 2 else 0,
            1 if row[8] == 1 else 0,
            # 1 if row[9] == 2 else 0,
            0,
            1 if row[9] == 1 else 0,
            row[0],
            row[1] if row[1] !="" else "No Title",
            row[2],
            row[6],
            0 if row[5] == "0001-01-01T00:00:00" else 1000*int(datetime.fromisoformat(row[5]).replace(tzinfo=desired_timezone).timestamp()),
            row[4],
            '[]',
            0,
            1,
            row[3],
            "",
            "."
        )
        for row in rows
    ]
    
    # Insert the transformed data into the second table
    cursor2.executemany(insert_query, transformed_rows)

    # Commit the transaction
    condest.commit()
    
    # Close the connections
    cursor1.close()
    con.close()
    cursor2.close()
    condest.close()

    
else:
    print("this is a CLI tool, please use it on a proper shell")
