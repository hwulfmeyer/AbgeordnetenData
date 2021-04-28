import math
import re
from datetime import datetime
from dateutil import relativedelta
from os import listdir, path, mkdir
from os.path import isfile, join
import matplotlib.pyplot as plt
import pandas as pd
import requests
from bs4 import BeautifulSoup

plt.close("all")

FOLDER = path.dirname(path.realpath('__file__')) + "\\abgeordneten\\"
mkdir(FOLDER)

EINKUNFTSSTUFEN = {'1': [1,3.5],
                    '2': [3.5,7],
                    '3': [7,15],
                    '4': [15,30],
                    '5': [30,50],
                    '6': [50,75],
                    '7': [75,100],
                    '8': [100,150],
                    '9': [150,250],
                    '10': [250,math.inf]}

DATEN = {'name': [], 'partei': [], 'beruf': [], 'nebenverdienst_min': [], 'neberverdienst_max': []}

BEGIN_LEGISLATUR = datetime.strptime(str('24.10.2017'), '%d.%m.%Y')


def downloadAbgeordnetenBiografien():
    listurl = "https://www.bundestag.de/ajax/filterlist/de/abgeordnete/biografien/525246-525246?limit=9999&view=BTBiographyList"
    response = requests.get(listurl)

    if response is None or response.status_code != 200:
        print("Nothing found, status:" + str(response.status_code))
    else:
        abg_urls = []
        listitems = BeautifulSoup(response.text, "html.parser").find_all(name='li')
        for item in listitems:
            abg_url = BeautifulSoup(str(item), "html.parser").find(name='a', attrs={'class' : 'bt-open-in-overlay'}).get('href').encode('utf-8').decode('utf-8')
            abg_urls.append(abg_url)
        

    for url in abg_urls:
        abg_url = "https://www.bundestag.de" + url + "?view=main"
        response = requests.get(abg_url)
        if response is None or response.status_code != 200:
            print("Nothing found, status:" + str(response.status_code))
        else:
            path = url.replace("/","")
            with open(FOLDER + path + ".html", 'wb') as f:
                f.write(response.content)
            print("download: " + path)

def getFiles():
    files = [f for f in listdir(FOLDER) if isfile(join(FOLDER, f))]
    return files

def datamineFiles():
    for path in getFiles():
        with open(FOLDER + path, 'rb') as f:
            htmlfile = f.read()
            eckdaten = BeautifulSoup(htmlfile, "html.parser").find(name='div', attrs={'class' : 'col-xs-8 col-md-9 bt-biografie-name'})
            name = re.search(r"<h3>\s*(.*),\s.*\s*\S*<\/h3>", str(eckdaten.contents)).group(1)
            party = re.search(r"<h3>\s*.*,\s(.*)\s*\S*<\/h3>", str(eckdaten.contents)).group(1)
            beruf = BeautifulSoup(str(eckdaten.contents), "html.parser").find(name='div', attrs={'class' : 'bt-biografie-beruf'}).find(name='p')

            DATEN['name'].append(name)
            DATEN['partei'].append(party)
            if len(beruf.contents) != 0:
                DATEN['beruf'].append(beruf.contents[0])
            else:
                DATEN['beruf'].append('')
            
            angaben_text = BeautifulSoup(htmlfile, "html.parser").find(name='div', attrs={'id' : 'bt-angaben-collapse'})
            angabenstufen = re.findall(r"(jährlich|monatlich|[0-9]{4})?[,]?\s?Stufe\s?([0-9]{1,2})\s?(\(bis\s?([0-9]{2}.[0-9]{2}.[0-9]{4})?\))?", str(angaben_text.contents))
            
            nebenverdienst_min = 0
            nebenverdienst_max = 0
            if len(angabenstufen) != 0:
                stufendict = {}
                for stufen in angabenstufen:
                    dictkey = stufen[1]
                    if dictkey == '12': #gregory gysi site error
                        dictkey = '1'
                    multiplicator = 1.0
                    if stufen[0] in ['monatlich', 'jährlich']:
                        if stufen[2] != '':
                            BIS = datetime.strptime(str(stufen[3]), '%d.%m.%Y')
                            r = relativedelta.relativedelta(BIS, BEGIN_LEGISLATUR)
                            if stufen[0] in ['monatlich']:
                                multiplicator = r.months + (r.days/30)
                            if stufen[0] in ['jährlich']:
                                multiplicator = r.years + (r.months/12)
                    if dictkey in stufendict:
                        stufendict[dictkey] += 1*multiplicator
                    else:
                        stufendict[dictkey] = 1*multiplicator

                for key, value in stufendict.items():
                    nebenverdienst_min += EINKUNFTSSTUFEN[key][0]*value
                    nebenverdienst_max += EINKUNFTSSTUFEN[key][1]*value
                nebenverdienst_min *=1000
                nebenverdienst_max *=1000
            DATEN['nebenverdienst_min'].append(int(nebenverdienst_min))
            DATEN['neberverdienst_max'].append(nebenverdienst_max)
    
    return DATEN



downloadAbgeordnetenBiografien()
DATENDICT = datamineFiles()

df = pd.DataFrame.from_dict(DATENDICT)
df = df.sort_values(by=['nebenverdienst_min'], ascending=False)

df.head(40).plot(y="nebenverdienst_min", x='name', kind='barh')
plt.show()


