import re
from os import listdir, path
from os.path import isfile, join

import requests
from bs4 import BeautifulSoup

FOLDER = path.dirname(path.realpath('__file__')) + "/abgeordneten/"

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
            name = re.search("<h3>\s*(.*),\s.*\s*\S*<\/h3>", str(eckdaten.contents))
            party = re.search("<h3>\s*.*,\s(.*)\s*\S*<\/h3>", str(eckdaten.contents))
            print(str(name.group(1)) + " " + str(party.group(1)))
            beruf = BeautifulSoup(str(eckdaten.contents), "html.parser").find(name='div', attrs={'class' : 'bt-biografie-beruf'}).find(name='p')
            if len(beruf.contents) != 0:
                print(beruf.contents[0])
            angaben = BeautifulSoup(htmlfile, "html.parser").find(name='div', attrs={'id' : 'bt-angaben-collapse'})
            angabenstufen = re.findall("(jährlich|monatlich|[0-9]{4})?[,]?\sStufe\s([0-9]{1,2})", str(angaben.contents))
            print(angabenstufen)

#downloadAbgeordnetenBiografien()
datamineFiles()


