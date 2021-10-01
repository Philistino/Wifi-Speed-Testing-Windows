import os
import json
import time
from csv import DictWriter
from datetime import datetime
import subprocess

# CSV to track results
data_file_name = 'iperf_test_data.csv'

# Path to iperf3 client
iperf3_client = 'C:\\iperf-3.1.3-win64\\iperf3.exe'

# List your preferred network first to reconnect to it after testing
test_ssids = ['It Hurts When IP', 'Nacho Wifi']

# -t = time in seconds for test, -P = parallel streams, -O = omit first seconds ramping, -i = seconds between throughput reports - use 0 to disable
iperf3_args = ['-t 10', '-P 10', '-O 5', '-i 0']

# Locations to test from
locations = {'1' : 'Couch',
            '2' : 'Office', 
            '3' : 'Table', 
            '4' : 'Bed', 
            '5' : 'Kitchen'}

networks =  {'It Hurts When IP': 
                {'ssid' : 'It Hurts When IP',
                'server_ip' : '192.168.1.101',
                'server_port' : '-p 5201'},
            'Nacho Wifi': 
                {'ssid' : 'Nacho Wifi',
                'server_ip' : '10.10.4.2',
                'server_port' : '-p 5201'}}

def data_in_same_dir(file_name):
    # Set save location to data file in same folder as python script
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))
    global data_file
    data_file = os.path.join(__location__, file_name)

def run_iperf3_client(network, location):
    print('Running test for: '+  iperf3_args[0].split(' ')[-1] + 's')

    s = subprocess.check_output(
        [iperf3_client, '-J', '-c', networks[network]['server_ip'], networks[network]['server_port']] + iperf3_args)

    results = json.loads(s)
    d = {
        'date' : datetime.now().strftime("%a %b %d %Y"),
        'time' : datetime.now().strftime("%H:%M:%S %Z"),
        'local_host' : results['start']['connected'][0]['local_host'],
        'remote_host' : results['start']['connected'][0]['remote_host'],
        'sent_speed' : round(results['end']['sum_sent']['bits_per_second']/1000000),
        'received_speed' : round(results['end']['sum_received']['bits_per_second']/1000000),
        'test_duration' : round(results['end']['sum_sent']['seconds']),
        'location' : location,
        'network' : networks[network]['ssid']
        }
    print(d)
    return d
    
def write_to_csv(d):
    # Create list of column names from dictionary keys
    columns = list(d)

    # Create file if it does not already exist
    if not os.path.isfile(data_file):
        with open(data_file, mode='w', newline='') as iperfcsv:
            print('Creating data file...')
            csv_writer = DictWriter(iperfcsv, fieldnames=columns)
            csv_writer.writeheader()

    # Append row of dictionary values
    with open(data_file, 'a', newline='') as iperfcsv:
        # Pass the file object and a list of column names to DictWriter() and create an object of DictWriter
        dictwriter_object = DictWriter(iperfcsv, fieldnames=columns)
        #Pass the dictionary as an argument to the Writerow()
        dictwriter_object.writerow(d)
        
def test_networks():
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
        write_to_csv(run_iperf3_client(network, locations[place]))
    # Reconnect to default network
    time.sleep(3)
    os.system(f'''cmd /c "netsh wlan connect name={test_ssids[0]}"''')

data_in_same_dir(data_file_name)
test_networks()

import pandas as pd
df = pd.read_csv(data_file)
print("\n")
print('iperf3 minimums:')
print(df[['location', 'network', 'received_speed']].groupby(['location','network']).min())

print("\n")
print('iperf3 maximums:')
print(df[['location', 'network', 'received_speed']].groupby(['location','network']).max())

print("\n")
print('iperf3 averages:')
print(df[['location', 'network', 'received_speed']].groupby(['location','network']).mean())
