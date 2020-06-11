#!/usr/bin/env python3

import requests
import re
import pickle
import sys
import time
from bs4 import BeautifulSoup

def getCityLinks(url, city_localizer):
    try:
        response = requests.get(url, timeout=5)
    except:
        print(f"Failed to load {url}")
        return None
    soup = BeautifulSoup(response.text, "html.parser")
    links = []
    content = soup.find("div", {"id": "mw-content-text"})
    tables = content.findChildren("div", recursive = False)[0].findChildren("table", recursive=True)
    for table in tables:
        cities = city_localizer(table)
        if cities:
            return cities
    print(f"Did not find city table for {url}")
    return None

def getWorldCities(table):
    txt = table.get_text().lower()
    if "tokyo" in txt:
        links = []
        rows = table.findChildren("tr", recursive = True)
        for row in rows:
            tds = row.findChildren("td", recursive = False)
            if len(tds) > 0:
                a_s = tds[0].findChildren("a", recursive = False)
                for a in a_s:
                    href = str(a.get('href'))
                    links.append(href.split("/wiki/")[1])
        return links
    return None

def getUSCities(table):
    txt = table.get_text().lower()
    if "louisville" in txt:
        links = []
        rows = table.findChildren("tr", recursive = True)
        for row in rows:
            tds = row.findChildren("td", recursive = False)
            if len(tds) > 0:
                a_s = tds[1].findChildren("a", recursive = True)
                for a in a_s:
                    href = str(a.get('href'))
                    if href[:5] == '/wiki':
                        links.append(href.split("/wiki/")[1])
        return links
    return None

def getNZCities(table):
    txt = table.get_text().lower()
    if "auckland" in txt:
        links = []
        rows = table.findChildren("tr", recursive = True)
        for row in rows:
            tds = row.findChildren("td", recursive = False)
            if len(tds) > 0:
                a_s = tds[1].findChildren("a", recursive = True)
                for a in a_s:
                    href = str(a.get('href'))
                    if href[:5] == '/wiki':
                        links.append(href.split("/wiki/")[1])
        return links
    return None

def getAUSCities(table):
    txt = table.get_text().lower()
    if "canberra" in txt:
        links = []
        rows = table.findChildren("tr", recursive = True)
        for row in rows:
            tds = row.findChildren("td", recursive = False)
            if len(tds) > 0:
                a_s = tds[1].findChildren("a", recursive = True)
                for a in a_s:
                    href = str(a.get('href'))
                    if href[:5] == '/wiki':
                        links.append(href.split("/wiki/")[1])
    return None

def getCANCityLinks():
    txt = table.get_text().lower()
    if "toronto" in txt:
        links = []
        rows = table.findChildren("tr", recursive = True)
        for row in rows:
            tds = row.findChildren("td", recursive = False)
            if len(tds) > 0:
                a_s = tds[1].findChildren("a", recursive = True)
                for a in a_s:
                    href = str(a.get('href'))
                    if href[:5] == '/wiki':
                        links.append(href.split("/wiki/")[1])
        return links
    return None

def getClimateTable(link):
    try:
        response = requests.get("https://en.wikipedia.org/wiki/" + link, timeout=5)
    except:
        print(f"Failed to load page: https://en.wikipedia.org/wiki/{link}")
        return None
    soup = BeautifulSoup(response.text, "html.parser")
    links = []
    content = soup.find("div", {"id": "mw-content-text"})
    tables = content.findChildren("div", recursive = False)[0].findChildren("table", recursive=True)
    weather_tables = []
    for table in tables:
        txt = table.get_text().lower()
        if "climate" in txt and ("mean maximum" in txt or "average high" in txt):
            weather_tables.append(table)
    if len(weather_tables) == 0:
        print(f"Found 0 potential weather tables for the page on {link}.")
        return 0
    if len(weather_tables) > 1:
        print(f"Found {len(weather_tables)} potential weather tables for the page on {link}. Proceeding with the first one.")
    return weather_tables[0]

def getDataFromTr(tr, celcius):
    data = []
    tds = tr.findChildren("td", recursive=False)
    for td in tds:
        if celcius:
            try:
                data.append(float(td.get_text().split("(")[0].rstrip("\n").replace("−", "-").replace(",", "")))
            except:
                return None
        else:
            try:
                data.append(float(td.get_text().split("(")[-1].split(")")[0].rstrip("\n").replace("−", "-").replace(",", "")))
            except:
                return None
    return data

def getClimateData(table):
    celcius = True
    if "(°C)" in table.get_text():
        celcius = False
#    print(f"Primary units listed are in {'Celcius' if celcius else 'Fahrenheit'}.")
    mean_max = None
    avg_high = None
    mean = None
    avg_low = None
    mean_min = None
#    precip = None
    trs = table.findChildren("tr", recursive = True)
    for tr in trs:
        if len(tr.findChildren("td")) > 1:
            tr_txt = tr.get_text().lower()
            if "mean maximum" in tr_txt:
                data = getDataFromTr(tr, celcius)
                if data:
                    mean_max = data
            elif "average high" in tr_txt:
                data = getDataFromTr(tr, celcius)
                if data:
                    avg_high = data
            elif "daily mean" in tr_txt:
                data = getDataFromTr(tr, celcius)
                if data:
                    mean = data
            elif "average low" in tr_txt:
                data = getDataFromTr(tr, celcius)
                if data:
                    avg_low = data
            elif "mean minimum" in tr_txt:
                data = getDataFromTr(tr, celcius)
                if data:
                    mean_min = data
#           elif "precipitation" in tr_txt:
#               precip = getDataFromTr(tr, celcius)
#    print(mean_max, avg_high, mean, avg_low, mean_min)
    return mean_max, avg_high, mean, avg_low, mean_min

def calculateDesirabilityScore(mean_max, avg_high, mean, avg_low, mean_min):
    score = 0
    not_nones = 0
    if mean_max:
        not_nones += 1
        for temp in mean_max:
            if temp > 30:
                score += max(0, 1-(temp-30)/5)
            elif temp < 20:
                score += max(0, 1-(20-temp)/5)
            else:
                score += 1
    if avg_high:
        not_nones += 1
        for temp in avg_high:
            if temp > 23:
                score += max(0, 1-(temp-23)/5)
            elif temp < 15:
                score += max(0, 1-(15-temp)/5)
            else:
                score += 1
    if mean:
        not_nones += 1
        for temp in mean:
            if temp > 20:
                score += max(0, 1-(temp-20)/5)
            elif temp < 8:
                score += max(0, 1-(8-temp)/5)
            else:
                score += 1
    if avg_low:
        not_nones += 1
        for temp in avg_low:
            if temp > 18:
                score += max(0, 1-(temp-18)/5)
            elif temp < 5:
                score += max(0, 1-(5-temp)/5)
            else:
                score += 1
    if mean_min:
        not_nones += 1
        for temp in mean_min:
            if temp > 15:
                score += max(0, 1-(temp-15)/5)
            elif temp < 0:
                score += max(0, 1-(0-temp)/5)
            else:
                score += 1
    return (score * 5 / not_nones) / 65

if __name__ == "__main__":
    locations = sys.argv[1:]
    links = []
    for location in locations:
        if location == "us":
            links += getCityLinks("https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population", getUSCities)
        elif location == "nz":
            links += getCityLinks("https://en.wikipedia.org/wiki/List_of_cities_in_New_Zealand", getNZCities)
        elif location == "world":
            links += getCityLinks("https://en.wikipedia.org/wiki/List_of_largest_cities", getWorldCities)
        elif location == "aus":
            links += getCityLinks("https://en.wikipedia.org/wiki/List_of_cities_in_Australia_by_population", getAUSCities)
        elif location == "can":
            links += getCityLinks()

    link_dic = {link: 0 for link in links}
    for link in links:
        print(f"Getting climate data from {link}")
        table = getClimateTable(link)
        if table:
            mean_max, avg_high, mean, avg_low, mean_min = getClimateData(table)
            desirability_score = calculateDesirabilityScore(mean_max, avg_high, mean, avg_low, mean_min)
            print(f"My climate score for {link}: {desirability_score}")
            link_dic.update({link: desirability_score})
    scores = []
    for x in link_dic.values():
        if x not in scores:
            scores.append(x)
    scores.sort()
    for score in scores:
        for link in link_dic:
            if link_dic[link] == score:
                print(f"{link}: {score}/1")
