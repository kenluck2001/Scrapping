import sys  

reload(sys)  
sys.setdefaultencoding('utf8')

import requests as req
import lxml
from lxml import html
import json
import re
import pandas as pd
import numpy as np
import re 
import datetime
from lxml.html.clean import Cleaner

cleaner = Cleaner()
cleaner.javascript = True # This is True because we want to activate the javascript filter
cleaner.style = True      # This is True because we want to activate the styles & stylesheet filter



class ScraperFilter ():
    base_url = 'http://www.f150ecoboost.net/forum/42-2015-ford-f150-ecoboost-chat'
    totalPages = 0

    listOfURL  = [] 
    listNameOfThread  = []
    listViews  = []
    listReplies  = []
    listPostTime  = []
    listPostDate = []

    def __init__(self):
        '''
            Constructor
        '''
        r = req.get(self.base_url)

        tree = lxml.html.fromstring( cleaner.clean_html(r.content) )
        contentLabel = tree.findall(".//span/a[@class='popupctrl']") #get
        pageList = [ el.text_content() for el in contentLabel]
        totalNumOfPages = pageList[0].split()[-1]
        self.totalPages = int (totalNumOfPages)


    def readCurrentURL(self, url):
        """
            get current page content
        """
        r = req.get(url)

        tree = lxml.html.fromstring( cleaner.clean_html(r.content) )
        content = tree.findall(".//a[@class='title']") #get informative text

        list_of_urls = [ el.get('href') for el in content ] 
        list_name_of_thread = [ el.text_content() for el in content]

        content = tree.findall(".//ul[@class='threadstats td alt']/li")
        list_replies_and_views = [ el.text_content() for el in content]

        list_replies = [ int (list_replies_and_views[ind].split( )[-1].replace('', '0').replace(',', '').encode("ascii", "ignore") )   for ind in range( 0, len(list_replies_and_views), 3 )]

        list_views = [ int (list_replies_and_views[ind].split( )[-1].replace('', '0').replace(',', '').encode("ascii", "ignore"))   for ind in range( 1, len(list_replies_and_views), 3 )]

        contentLabel = tree.findall(".//dl[@class='threadlastpost td']") #get
        list_post_date_time = [ el.text_content() for el in contentLabel]

        list_post_date = [obj.split()[4][:-1] if len(obj.split()) >= 4 else '' for obj in list_post_date_time ]

        list_post_time = [obj.split()[5] + obj.split()[6] if len(obj.split()) >= 4 else '' for obj in list_post_date_time ]

        list_post_date_indx = [ind for ind, x in enumerate(list_post_date) if x == "Yesterday" ]

        for ind in list_post_date_indx: 
            list_post_date[ind] = self.getYesterDay( )

        #link_to_thread, name_of_thread, views, replies, last_post_time, last_post_date

        return list_of_urls, list_name_of_thread, list_views,list_replies, list_post_time, list_post_date


    def getEveryURLContent(self):
        """
            get content of every pagination
        """

        for page in range (self.totalPages):
            currentURL = self.base_url + "/index"+ str(page+1) + ".html"
            list_of_urls, list_name_of_thread, list_views,list_replies, list_post_time, list_post_date = self.readCurrentURL( currentURL )

            self.listOfURL.extend ( list_of_urls )
            self.listNameOfThread.extend ( list_name_of_thread )
            self.listViews.extend ( list_views )
            self.listReplies.extend ( list_replies )
            self.listPostTime.extend ( list_post_time )
            self.listPostDate.extend ( list_post_date )

        #write to csv
        self.convertToCSV ()



    def getYesterDay(self):
        yesterDay = datetime.datetime.now() - datetime.timedelta(days=1)
        return yesterDay.strftime("%m-%d-%y")



    def convertToCSV (self):
        """
            write to CSV
        """

        labels = ["link_to_thread", "name_of_thread", "views", "replies", "last_post_time", "last_post_date"]

        df = pd.DataFrame(columns=labels)


        for i in range(len (self.listOfURL)):
            df.loc[i] = [self.listOfURL[i], self.listNameOfThread[i], self.listViews[i], self.listReplies[i], self.listPostTime[i], self.listPostDate[i]]


        df[["views", "replies"]] = df[["views", "replies"]].astype("int")

        #sort by views
        df = df.nlargest(100, "views")

        df.to_csv("scraper.csv", header=True,  index=False)


if __name__ == "__main__":
    scrapObj = ScraperFilter ()
    scrapObj.getEveryURLContent( )


