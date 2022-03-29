import os, sys, json, bs4, pathlib
import numpy as np
import pandas as pd

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


if __name__ == "__main__":
    makeIndex()