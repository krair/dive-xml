#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Give a str to getLatLon() of a location to get a tuple of (latitude, longitude, formatted address)

@author: kitrairigh
"""
import urllib.request, urllib.parse, urllib.error, json

key = input('Enter your API key: \n')
serviceURL = 'https://maps.googleapis.com/maps/api/geocode/json?'

def getLatLon(address):
    if len(address) < 1:
        print('Invalid')
        return
    url = serviceURL + urllib.parse.urlencode({'address': address}) + '&key='+key
    
    data = urllib.request.urlopen(url)
    rec = data.read().decode()
    
    try:
        js = json.loads(rec)
    except:
        js = None
    
    if not js or js['status'] != 'OK' or 'status' not in js:
        print('======= FAILURE TO RECIEVE =======')
        return 
    lat = js['results'][0]['geometry']['location']['lat']
    lon = js['results'][0]['geometry']['location']['lng']
    loc = js['results'][0]['formatted_address']
    return (lat,lon,loc)