import csv
import json
import time
import toml
import argparse
import speedtest
import subprocess
import pandas as pd
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod


config = toml.load(Path(Path(__file__).parent, "config.toml"))


def get_args():
    parser = argparse.ArgumentParser(
        description="Test wireless network speeds. Primary commands are iperf3 and speedtest."
    )
    parser.add_argument(
        "test",
        default="",
        choices=["both", "iperf3", "speedtest"],
        help="Test(s) to perform",
    )
    parser.add_argument(
        "--rounds",
        required=False,
        default=1,
        help="Number of rounds of tests per network",
    )
    parser.add_argument(
        "--location",
        required=True,
        default="",
        choices=config["locations"],
        help=f"Location of device running test. options include: {str(config['locations'])}",
    )
    return parser.parse_args()


def current_wifi_network():
    """Returns current wifi network connected to on Windows
    Returns: string
    """
    cmd = ["netsh", "wlan", "show", "network"]
    r = subprocess.run(cmd, capture_output=True, text=True).stdout
    ls = r.split("\n")
    return next(v.strip() for k, v in (p.split(":") for p in ls if "SSID" in p))


def connect_to_network(ssid):
    """Connects to given ssid
    Returns: bool True if connected
    """
    cmd = ["netsh", "wlan", "connect", f"name={ssid}"]
    output = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
    time.sleep(5)
    return "Connection request was completed successfully." in output


def throughput_analysis(test_type, csv_file):
    """Prints std dev and mean for each network and location combination"""
    df = pd.read_csv(csv_file)
    print(f"\n{test_type} standard deviation:")
    print(df.groupby(["location", "network"]).std())
    print(f"\n{test_type} averages:")
    print(df.groupby(["location", "network"]).mean())


class CSVWriter:
    def __init__(self, file_path, dict_) -> None:
        self.file_path = Path(file_path)
        self.dict_ = dict_
        self.file_exists = self.file_path.is_file()

    def write_data(self):
        """determines if the file exists and how to write to it"""
        if self.file_exists:
            return self.write_dict_to_csv(self.file_path, self.dict_)
        else:
            return self.create_csv_and_write_row_from_dict(self.file_path, self.dict_)

    def create_csv_and_write_row_from_dict(self, file_path, dict_):
        """create csv using dict keys as column names and write row with values
        Args:
            file_path: path to csv file
            dict_: dictionary to write to csv
        Returns: None
        """
        with open(file_path, mode="w", newline="") as f:
            dict_writer = csv.DictWriter(f, fieldnames=list(dict_))
            dict_writer.writeheader()
            dict_writer.writerow(dict_)

    def write_dict_to_csv(self, file_path, dict_):
        """append row to csv file from dictionary
        Args:
            file_path: path to csv file
            dict_: dictionary to write to csv
        Returns: None
        """
        with open(file_path, "a", newline="") as f:
            dict_writer = csv.DictWriter(f, fieldnames=list(dict_))
            dict_writer.writerow(dict_)


class Test(ABC):
    @abstractmethod
    def run_tests(self) -> list:
        """runs specified number of tests"""

    @abstractmethod
    def run_test(self) -> dict:
        """runs individual tests"""


class iperf3Tester(Test):
    def __init__(self, location, rounds):
        self.location = location
        self.rounds = rounds
        self.test_type = "iperf3"

    def run_tests(self):
        """controls how many times the test is run
        returns: list of results dicts
        """
        results = []
        for network in config["networks"].values():
            connect_to_network(network["ssid"])
            for _ in range(self.rounds):
                result = self.run_test(str(network["ssid"]))
                results.append(result)
        return results

    def run_test(self, network):
        """runs iperf3 client
        returns: dict of key results
        """
        cmd = [
            Path(config["iperf3_client"]),
            "-J",
            "-c",
            config["networks"][network]["iperf3_server_ip"],
            f"-p {config['networks'][network]['iperf3_server_port']}",
            "-i 0",
        ] + config["iperf3_args"]
        s = subprocess.check_output(cmd)
        results = json.loads(s)
        return {
            "date_time": datetime.now().isoformat(),
            "local_host": results["start"]["connected"][0]["local_host"],
            "remote_host": results["start"]["connected"][0]["remote_host"],
            "sent_speed": round(
                results["end"]["sum_sent"]["bits_per_second"] / 1000000
            ),
            "received_speed": round(
                results["end"]["sum_received"]["bits_per_second"] / 1000000
            ),
            "test_duration": round(results["end"]["sum_sent"]["seconds"]),
            "location": self.location,
            "network": config["networks"][network]["ssid"],
        }


class speedtestTester(Test):
    def __init__(self, location, rounds):
        self.location = location
        self.rounds = rounds
        self.test_type = "speedtest"

    def run_tests(self):
        """controls how many times the test is run
        returns: list of results dicts
        """
        results = []
        for network in config["networks"].values():
            connect_to_network(network["ssid"])
            for _ in range(self.rounds):
                result = self.run_test(str(network["ssid"]))
                results.append(result)
        return results

    def run_test(self, network):
        """runs speedtest
        returns: dict of results
        """
        servers = []
        threads = None
        s = speedtest.Speedtest()
        s.get_servers(servers)
        s.get_best_server()
        s.download(threads=threads)
        s.upload(threads=threads)
        s.results.share()
        results = s.results.dict()
        return {
            "date_time": datetime.now().isoformat(),
            "location": self.location,
            "network": network,
            "downspeed": round(results["download"] / 1000000),
            "upspeed": round(results["upload"] / 1000000),
            "ping": results["ping"],
        }


class TestRunner:
    def __init__(self, t: Test) -> None:
        self.test = t

    def record_results(self, results):
        data_file = Path(Path(__file__).parent, f"{self.test.test_type}_data.csv")
        for result in results:
            data_writer = CSVWriter(data_file, result)
            data_writer.write_data()
        return data_file

    def run_tests_and_process_results(self):
        results = self.test.run_tests()
        data = self.record_results(results)
        throughput_analysis(self.test.test_type, data)


def main():
    args = get_args()
    default_network = current_wifi_network()
    if args.test in ["iperf3", "both"]:
        test = iperf3Tester(args.location, int(args.rounds))
        tester = TestRunner(test)
        tester.run_tests_and_process_results()
    if args.test in ["speedtest", "both"]:
        test = speedtestTester(args.location, int(args.rounds))
        tester = TestRunner(test)
        tester.run_tests_and_process_results()
    if current_wifi_network() != default_network:
        connect_to_network(default_network)


if __name__ == "__main__":
    main()
