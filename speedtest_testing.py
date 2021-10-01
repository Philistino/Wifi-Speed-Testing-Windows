import os
import json
import time
from csv import DictWriter
from datetime import datetime
import speedtest

# csv to track results
data_file_name = 'speedtest_test_data.csv'

# List your preferred network first to reconnect to it after testing
test_ssids = ['It Hurts When IP', 'Nacho Wifi']

# Locations to test from
locations = {
            '1' : 'Couch',
            '2' : 'Office', 
            '3' : 'Table', 
            '4' : 'Bedroom', 
            '5' : 'Kitchen'
            }

def data_in_same_dir(file_name):
    # Set save location to data file in same folder as python script
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))
    global data_file
    data_file = os.path.join(__location__, file_name)

def run_speedtest(network, location):
    print('Running test for: ' + network + ' at ' + location)
    s = speedtest.Speedtest()   
    date = datetime.now().strftime("%a %b %d %Y")
    time = datetime.now().strftime("%H:%M:%S")
    downspeed = round(s.download() / 1000000)
    print('Downspeed: ' + str(downspeed))
    upspeed = round(s.upload() / 1000000)
    print('Upspeed: ' + str(upspeed))
    d = {
        'date': date,
        'time': time,
        'location': location,
        'network': network,
        'downspeed': downspeed,
        "upspeed": upspeed
        }
    return d

def write_to_csv(d):
    # Create list of column names from dictionary keys
    columns = list(d)

    # Create file if it does not already exist
    if not os.path.isfile(data_file):
        with open(data_file, mode='w', newline='') as speedcsv:
            csv_writer = DictWriter(speedcsv, fieldnames=columns)
            csv_writer.writeheader()

    # Append row of dictionary values
    with open(data_file, 'a', newline='') as speedcsv:
        # Pass the file object and a list of column names to DictWriter() and create an object of DictWriter
        dictwriter_object = DictWriter(speedcsv, fieldnames=columns)
        #Pass the dictionary as an argument to the Writerow()
        dictwriter_object.writerow(d)

def test_networks():
    # Get location input from user
    while True:
        # show places locations dictionary and get user input
        place = input("Enter location: " + json.dumps(locations))
        # check if place is equal to one of the dictionary keys and break once eligible option is selected 
        if place in locations.keys():
            break
    print(locations[place])
    for network in test_ssids:
        os.system(f'''cmd /c "netsh wlan connect name={network}"''')
        print('Connecting to: ' + network)
        time.sleep(15)
        # run functions
        write_to_csv(run_speedtest(network, locations[place]))
    # Reconnect to default network
    time.sleep(3)
    os.system(f'''cmd /c "netsh wlan connect name={test_ssids[0]}"''')

data_in_same_dir(data_file_name)
test_networks()

import pandas as pd
df = pd.read_csv(data_file)
print("\n")
print('speedtest averages:')
print(df.groupby(['location','network']).mean())
