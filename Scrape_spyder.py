# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 09:50:12 2020

@author: eli
"""

import requests
import os
import requests
import json
import zipfile
import pandas as pd
import numpy as np

###
#Using some clever string indexing, loop through json download links for the 
#NHTSA Oblique tests
###
oblique_tests = pd.read_csv('oblique_tests_trunc.csv', dtype='str')

for index, row in oblique_tests.iterrows():
    link = 'https://www-nrd.nhtsa.dot.gov/database/vsr/download.aspx?tstno=%s&curno=&database=v&name=v%s&format=json'%(row[0], row[0])
    print(link)
    
    response = requests.get(url=link, allow_redirects=True)
    with open(row[0]+'.zip', 'wb') as fd:
        fd.write(response.content)
    # json_response = response.json()
    # print(json_response)
    
    # with open(index)
# Read in the downloaded Json file.  Note it works if a series, not frame

'''Next to do is to get from this request object to the json file.  Maybe a way
to do this without downloading / reading into memory?  At the end of the day, my goal is 
to have some large file with all tests and accelerations.'''

data_df = pd.read_json(
    'v07467.json', 
    orient='records', 
    typ='series',
    convert_dates=False
    )

# Pull the instrumentation data
inst = pd.DataFrame(data_df['INSTRUMENTATION'])

#filter for only the sensors at the vehicle CG
inst_filtered = inst[inst['SENATTD'] == 'VEHICLE CG']

test = inst_filtered["URL_TSV"][174]

test_request = requests.get(test, allow_redirects=True)

with open('test_file', 'wb') as f:
    f.write(test_request._content)