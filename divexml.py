#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 28 17:04:37 2020

@author: kitrairigh
"""
# TODO - Create a check to see where the XML file came from. If subsurface, write
        # new code to break apart and fit into this model
# TODO - Softcode diver name input

from lxml import etree
import sqlite3, os, sys
import GmapsGPS

def cleanXML(root): # clean namespaces and empty space
    for elem in root.getiterator():
        elem.tag = etree.QName(elem).localname
        etree.cleanup_namespaces(root)
    return root

# Choose a folder of xml files or a single XML file
def getXMLlist():
    directory = ''
    files = []
    while True:
        filepath = input('Input directory or filepath: ')
        if os.path.isdir(filepath):
            files = sorted([i for i in os.listdir(filepath) if i.lower().endswith('xml')])
            print(f'Found {len(files)} XML files in {filepath}')
            yn = input('Proceed? (y/n)')
            if yn != 'y': sys.exit()
            return files, filepath
        elif os.path.isfile(filepath) and filepath.lower().endswith('xml'):
            directory = os.path.dirname(filepath)
            files.append(os.path.basename(filepath))
            return files, directory
        else:
            print('Invalid, please try again')
        

# connect to db
connection = sqlite3.connect('/Users/kitrairigh/Documents/Diving/Log/DiveLogdb.sqlite')
cur = connection.cursor()
counter = 0
while True:
    myFiles, directory = getXMLlist() # filename retrieval
    for item in myFiles:
        file = open(os.path.join(directory, item))
        
        # clean xml, pull basic dive data, create list of dive samples
        tree = cleanXML(etree.fromstring(file.read()))
        diveDict = {k.tag:k.text for k in tree if k.tag != 'SampleBlob'}
        if diveDict["Mode"] == '3': continue #ignore freedives
        samples = tree.findall('DiveSamples/Dive.Sample')
        print(f'Dive on {diveDict["StartTime"]} and was {int(diveDict["Duration"])//60} minutes')
        if input('Proceed to place in db? (y/n) ') != 'y': continue 
        
        # Begin to push data to db
        cur.execute('SELECT id FROM DiveLog WHERE date=?',(diveDict['StartTime'],))
        log_id = cur.fetchone()
        
        if log_id is not None:
            print('This dive is already stored in the database!')
            continue
        # Get a location from input, call gmaps to get GPS and formatted name
        location = input('Enter a location for this dive: ')
        loc = GmapsGPS.getLatLon(location)
    
        # Dive computer information
        computer = f'{diveDict["Source"]} v.{diveDict["Software"]} - {diveDict["SerialNumber"]}'
    
        # Write raw data blob into db
        cur.execute('Insert Into RawData(xml) values (?)',(etree.tostring(tree).decode(),))
    
        # Write dive into dive log, get id for samples - HARD CODED 'KIT'
        cur.execute('''Insert OR IGNORE Into DiveLog(diver,date,avgdepth,bottomtemp,duration,maxdepth,sampleinterval,location,lat,lon,computer)
                    values (?,?,?,?,?,?,?,?,?,?,?)''',(
                    'Kit',diveDict['StartTime'],float(diveDict['AvgDepth']),float(diveDict['BottomTemperature']),
                    int(diveDict['Duration']),float(diveDict['MaxDepth']),int(diveDict['SampleInterval']),
                    loc[2],loc[0],loc[1],computer))
        cur.execute('SELECT id FROM DiveLog WHERE date=?',(diveDict['StartTime'],))
        log_id = cur.fetchone()[0]
        connection.commit()
    
        # Loop through samples list, write to 
        x = 20
        for i in samples:
            x-=1
            depth = float(i[2].text)
            temp = round(float(i[7].text),1)
            time = int(i[8].text)
            cur.execute('Insert into DiveSamples (id,time,depth,temperature) values(?,?,?,?)',
                        (log_id,time,depth,temp))
            if x == 0:
                connection.commit()
                x = 20
        connection.commit()
        counter += 1
    break
print(f'Complete, {counter} dives entered into db!')