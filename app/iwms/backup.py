#!/usr/bin/python

###########################################################
#
# This python script is used for mysql database backup
# using mysqldump and tar utility.
#
# Written by : Rahul Kumar
# Website: http://tecadmin.net
# Created date: Dec 03, 2013
# Last modified: Aug 17, 2018 
# Tested with : Python 2.7.15 & Python 3.5
# Script Revision: 1.4
#
##########################################################

# Import required python libraries

import os
import time
import datetime
import pipes
from dotenv import load_dotenv

def backup():
    basedir = os.path.abspath(os.path.dirname(__file__))
    # MySQL database details to which backup to be done. Make sure below user having enough privileges to take databases backup.
    # To take multiple databases backup, create any file like /backup/dbnames.txt and put databases names one on each line and assigned to DB_NAME variable.

    load_dotenv()
    DB_HOST = os.environ.get('DATABASE_HOST')
    DB_USER = os.environ.get('DATABASE_USER')
    DB_USER_PASSWORD = os.environ.get('PA_PASSWORD')
    DB_NAME = os.environ.get('DATABASE_NAME')
    BACKUP_PATH = basedir

    # Getting current DateTime to create the separate backup folder like "20180817-123433".
    DATETIME = time.strftime('%Y%m%d-%H%M%S')
    TODAYBACKUPPATH = BACKUP_PATH + '/' + DATETIME

    # Checking if backup folder already exists or not. If not exists will create it.
    try:
        os.stat(TODAYBACKUPPATH)
    except:
        os.mkdir(TODAYBACKUPPATH)

    # Code for checking if you want to take single database backup or assinged multiple backups in DB_NAME.
    print ("checking for databases names file.")
    if os.path.exists(DB_NAME):
        file1 = open(DB_NAME)
        multi = 1
        print ("Databases file found...")
        print ("Starting backup of all dbs listed in file " + DB_NAME)
    else:
        print ("Databases file not found...")
        print ("Starting backup of database " + DB_NAME)
        multi = 0

    # Starting actual database backup process.
    if multi:
        in_file = open(DB_NAME,"r")
        flength = len(in_file.readlines())
        in_file.close()
        p = 1
        dbfile = open(DB_NAME,"r")

        while p <= flength:
            db = dbfile.readline()   # reading database name from file
            db = db[:-1]         # deletes extra line
            dumpcmd = "mysqldump -h " + DB_HOST + " -u " + DB_USER + " -p" + DB_USER_PASSWORD + " " + db + " > " + pipes.quote(TODAYBACKUPPATH) + "/" + db + ".sql"
            os.system(dumpcmd)
            gzipcmd = "gzip " + pipes.quote(TODAYBACKUPPATH) + "/" + db + ".sql"
            os.system(gzipcmd)
            p = p + 1

        dbfile.close()
    else:
        db = DB_NAME
        dumpcmd = "mysqldump -h " + DB_HOST + " -u " + DB_USER + " -p" + DB_USER_PASSWORD + " " + db + " > " + pipes.quote(TODAYBACKUPPATH) + "/" + db + ".sql"
        os.system(dumpcmd)
        # gzipcmd = "gzip " + pipes.quote(TODAYBACKUPPATH) + "/" + db + ".sql"
        # os.system(gzipcmd)

    print ("")
    print ("Backup script completed")
    return TODAYBACKUPPATH, db + ".sql"