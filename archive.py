import os, sys, json, bs4, pathlib, pymysql
from alive_progress import alive_bar
import numpy as np
import pandas as pd
from fuzzywuzzy import fuzz


readpath = os.path.split(os.path.realpath(__file__))[0] + '/'
datafile = readpath + "data.json"

def getSoup(text):
    theSoup = bs4.BeautifulSoup(text, 'html.parser')
    return theSoup

def getData():
    with open(datafile, 'r', encoding='utf-8') as file:
        content = file.read()
    df = pd.json_normalize(json.loads(content))
    return df

def data_collect():
    if os.path.exists(datafile):
        print("[INFO] Data file exist.")
        return
    result = []
    for year in os.listdir(readpath):
        year_folder = readpath + year + '/'
        if not pathlib.Path(year_folder).is_dir():
            continue
        if "20" not in year:
            continue
        for month in os.listdir(year_folder):
            month_folder = year_folder + month + '/'
            if not pathlib.Path(month_folder).is_dir():
                continue
            for html_file in os.listdir(month_folder):
                info = {"year": year, "month": month, "filename": html_file}
                if html_file == 'index.html':
                    continue
                with open(month_folder + html_file, 'r', encoding= 'utf-8') as file:
                    content = file.read()
                soup = getSoup(content)
                info['title'] = soup.select("title")[0].getText()
                info['date'] = soup.select(".timestamp")[0].getText()
                print("[%s] %s" % (info['date'], info['title']))
                result.append(info)
    print(len(result))
    with open(datafile, 'w', encoding='utf-8') as file:
        file.write(json.dumps(result))

def makeIndex():
    data_df = getData()
    # year
    years = data_df['year'].unique()
    #if "index.html" not in os.listdir(readpath):
    with open("index.html", 'w', encoding='utf-8') as file:
        text = '<center><font size="30">'
        for year in years:
            text += '<a href="./%s/index.html">%s</a><br>' % (year, year)
        text += "</font></center>"
        file.write(text)
    # month
    for year in years:
        year_path = readpath + year + '/'
        months = os.listdir(year_path)
        #if "index.html" not in year_path:
        with open(year_path + "index.html", 'w', encoding='utf-8') as file:
            text = '<center><font size="30">'
            for month in months:
                if month != "index.html":
                    text += '<a href="./%s/index.html">%s</a><br>' % (month, month)
            text += "</font></center>"
            file.write(text)
    # posts
    for year in years:
        year_path = readpath + year + '/'
        months = []
        for m in os.listdir(year_path):
            if m != "index.html":
                months.append(m)
        for month in months:
            month_path = year_path + month + '/'
            posts_df = data_df[data_df['year']==year][data_df['month']==month]
            with open(month_path + "index.html", 'w', encoding='utf-8') as file:
                text = '<font size="5">'
                for i in posts_df.index:
                    text += '<a href="./%s">%s</a><br>' % (posts_df["filename"][i], posts_df["title"][i])
                text += "</font>"
                file.write(text)

def match():
    df = getData()
    df_head10 = ''
    while True:
        keywords = input("keywords: ")
        try:
            index = int(keywords)
            print(df.loc[index, ['filename', 'year', 'month']])
            continue
        except:
            pass
        match_degree = []
        for i in df.index:
            title = df['title'][i]
            match_degree.append(fuzz.ratio(keywords, title))
        df_match = df.assign(match_degree = match_degree)
        df_head10 = df_match.sort_values(by=['match_degree'], ascending=False)[['match_degree', 'title']].iloc[0:10]
        print(df_head10)


def sqlinsert():
    df = getData()
    total = df.index[-1]
    db = pymysql.connect('192.168.0.106', 'root', 'p1234', 'web')
    cursor = db.cursor()
    with alive_bar(total, manual=True) as bar:
        for i in df.index:
            bar(i/total)
            checkCommand = "SELECT * from cltv WHERE id=%s;" % str(i)
            cursor.execute(checkCommand)
            data = cursor.fetchone()
            if data:
                #print('[INFO] index %s already inserted.' % str(i))
                continue
            title = pymysql.escape_string(df['title'][i])
            insertCommand = "INSERT INTO cltv (id, year, month, filename, title, date) values (%s, '%s', '%s', '%s', '%s', '%s');" % (str(i), df['year'][i], df['month'][i], df['filename'][i], title, df['date'][i])
            try:
                cursor.execute(insertCommand)
                db.commit()
            except:
                db.rollback()
                print("[INFO] Index %s insert failed." % str(i))
                print(insertCommand)
    db.close()

def sql_search(keyword):
    db = pymysql.connect('192.168.0.106', 'root', 'p1234', 'web')
    cursor = db.cursor()
    command = "SELECT * from cltv WHERE title LIKE '%%%s%%';" % keyword
    cursor.execute(command)
    data = cursor.fetchall()
    db.close()
    return data

if __name__ == "__main__":
    match()
