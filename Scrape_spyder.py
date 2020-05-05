# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 09:50:12 2020

@author: eli
"""

import requests
import os
import io
import requests
import json
import zipfile
import pandas as pd
import numpy as np
import scipy.signal
import matplotlib.pyplot as plt
#%%
def plot_frf(b,a):
    b, a = scipy.signal.butter(4, 100, 'low', analog=True)
    w, h = scipy.signal.freqs(b, a)
    plt.plot(w, 20 * np.log10(abs(h))) 
    plt.xscale('log')
    plt.title('Butterworth filter frequency response')
    plt.xlabel('Frequency [radians / second]')
    plt.ylabel('Amplitude [dB]')
    plt.margins(0, 0.1)
    plt.grid(which='both', axis='both')
    plt.axvline(100, color='green') # cutoff frequency
    plt.show()


def cfc( data, cfc_class, T):
    
    def J211(data, cfc_class, T):
        
        X = data
        Y = np.zeros_like(X)
        
        wd = 2*np.pi * cfc_class * 2.0775
        wa = (np.sin(wd * T/2)) / (np.cos(wd * T/2))
        a0 = wa**2 / (1 + np.sqrt(2)*wa + wa**2)
        a1 = 2*a0
        a2 = a0
        b1 = -2 * (wa**2 - 1) / (1 + np.sqrt(2)*wa + wa**2)
        b2 = (-1 + np.sqrt(2)*wa - wa**2) / (1 + np.sqrt(2)*wa + wa**2)

        for i in range(3, len(X)):
            Y[i] = a0*X[i] + a1*X[i-1] + a2*X[i-2] + b1*Y[i-1] + b2*Y[i-2]
            
        return Y

    Y2 = np.flip(
        J211(
            np.flip(
                J211(
                    data, cfc_class, T)),
            cfc_class, T)
        )
    return Y2
#%%
# Oblique tests are manually listed in a csv to be downloaded.  
# _trunc is a shortened list foir testing


def download_nhtsa_zip(csv_name):
    
    oblique_tests = pd.read_csv(csv_name, dtype='str')
    bad_zip = []
    
    for index, row in oblique_tests.iterrows():
        try:
            link = 'https://www-nrd.nhtsa.dot.gov/database/vsr/download.aspx?tstno=%s&curno=&database=v&name=v%s&format=json'%(row[0], row[0])
            # print(link)
            
            response = requests.get(url=link, allow_redirects=True)

            # Save the requested zip file locally as a zipped folder with json file
            # with open('v'+row[0]+'.zip', 'wb') as fd:
            #   fd.write(response.content)
            with open('v'+row[0]+'.zip', 'wb') as fd:
                fd.write(response.content)
                
                with zipfile.ZipFile(fd.name, 'r') as zd:
                    print(response.ok)
                    zd.extractall()
                # with zipfile.ZipFile('v'+row[0]+'.zip', 'w') as fd:
                #     fd.write(response.content)
        except:
            print(fd.name)
            
            print(row[0] + ' Was a bad zip')
            bad_zip.append(row[0])
    return bad_zip

bad_zip = download_nhtsa_zip('oblique_tests_trunc.csv')

#%%   
def download_test_data(filename):
    
    #expects filename of json to pull data from
    data_df = pd.read_json(
        filename,
        orient='index',
        typ='series',
        convert_dates=False
        )
    
    print(filename)
    # Pull the instrumentation data
    inst = pd.DataFrame(data_df['INSTRUMENTATION'])
    
    #filter for only the sensors at the vehicle CG
    inst_cg = inst[inst['SENATTD'] == 'VEHICLE CG']
    inst_filtered = inst_cg[inst_cg['VEHNO'] == '2']

    writer = pd.ExcelWriter('output2.xlsx', mode='a', engine='openpyxl')
    b, a = scipy.signal.butter(4, 391.5995243, 'low',analog=True)
    #Imma cheat and copy paste from James Sheet
    a = [0.000167292, 0.000334583, 0.000167292]
    b = [1.963083723, -0.963752889]

    
    for index, row in inst_filtered.iterrows():
        
        test = inst_filtered["URL_TSV"][index]
        
        test_request = requests.get(test, allow_redirects=True)
        
        col_names = [inst_filtered['XTYPE'][index], inst_filtered["INSCOM"][index]]
        
        rawData = pd.read_csv(
            io.StringIO((test_request.content).decode('cp1252', errors='ignore')),
            delimiter='\t',
            names=col_names,
            engine='python',
            skipfooter=1) #the footer seemed to have an NA value.  Just leave it out for test
        
        # sample_period = rawData.iloc[1,0] - rawData.iloc[0,0]
        
        #this may be slow pulling into array and back to series Will check
        
        filt_data = cfc(np.array(rawData.iloc[:,1]), 60, 5e-5)
        
        rawData['filtered'] = pd.Series(filt_data)
        
        save_name = inst_filtered['TSTNO'][index] \
            + '_' + inst_filtered['AXISD'][index]\
                + inst_filtered['CHSTATD'][index]
                # +'.csv'
                    # + '_' + inst_filtered['SENTYPD'][index] \
        # rawData.to_csv(save_name) #This works
        
        rawData.to_excel(writer, sheet_name=save_name) 
        # with open(save_name, 'w') as f:
        #     f.write(rawData)
    
        print(' Saving Tab' + save_name + ' from ' + filename)
        plt.figure()
        plt.plot(rawData.iloc[:,0],rawData)
        
    
    writer.save()  
    writer.close()
    return rawData
   
    
test_output = download_test_data("v07467.json")
#%%
success = 0
fail = 0
for file in os.listdir():
    if file.endswith('.json'):
        try:    
            data_out = download_test_data(file)
            success += 1
        except:
            print('error on file ' + file)
            fail += 1
#%%
# for file in os.listdir():
#     if file.endswith('.json'):

'''Probably want to make a big summary dataframe and save as excel for sharing'''
# with open('RX', 'wb') as f:
#     f.write(test_request._content)
# return rawData