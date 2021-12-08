# Wifi-Speed-Testing-Windows
CLI utility to test the download and upload speeds using iperf3 and/or speedtest of one or more wifi network on Windows. 

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-blue.svg?style=flat-square)](https://www.python.org/)

---



# Introduction

This script has three main functions:

1. Run speedtest and iperf3 tests a specified number of times at a specified location for networks listed in the config file.

2. Record the results to CSV files in the same directory as the script is saved.

3. Report the mean and standard deviation of cumulative tests by network and testing location.


# Requirements

1. Python 3.6 or newer.

2. speedtest-cli, pandas, and toml packages from pypi:
```
pip install speedtest-cli pandas toml
```
3. Valid config file saved in the same directory as the script. Please see the example.

4. iperf3 must be on your system and you must have a running iperf3 server on another system, which should be a wired device. Download iperf3 from the official site here: https://iperf.fr/iperf-download.php#windows.


# Usage

## Manual (CLI)

```
usage: py wlan_tester.py {"both", "iperf3", "speedtest"} [--rounds] [--location]
                 
positional arguments:
  {"both", "iperf3", "speedtest"}
                        "both": runs both speedtest and iperf3 tests one or more times each.
                        "iperf3": runs iperf3 test one or more times. Requires '--location' keyword argument.
                        "speedtest": runs speedtest test one or more times. Requires '--location' keyword argument.

keyword arguments:
  -h, --help            show this help message and exit.
  --location            location of the computer where the test is taking place. Must match one of the locations listed in config.
  --rounds              number of tests to perform for each test type.
```

## Example Command (CLI)
```
py "c:/Users/philistino/desktop/wlan_tester.py" both --location Office --rounds 3
```
***

