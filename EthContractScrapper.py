"""
This script scans etherscan.io or ftmscan.com for new Verified Smart Contracts and then
checks whether they have repos on Github using either contract address or contract name.
It looks for repositories written in Solidity. If a contract is found on Github a notification
with the repo link is sent to a specified Telegram chat. The script saves all the found contracts
in a .log file inside your working directory.

Usage:
python3 EthContractScrapper.py eth # for etherscan.io
python3 EthContractScrapper.py ftm # for ftmscan.com
"""

import os
import re
import logging
import copy

from time import sleep
from argparse import ArgumentParser
from atexit import register
from datetime import datetime
from dotenv import load_dotenv
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service

from helpers import (
    exit_handler_1,
    exit_handler_2,
    github_search,
    get_last_n_contracts,
    telegram_send_message,
    get_all_verified_contracts,
    get_all_search_contracts,
    CustomAction,
    formated,
    dict_complement_b,
    TextFormat,
)

# Set up arguments, values and settings for the CLI
software_ver = "1.1.0"
web_choices = ("etherscan.io", "ropsten.etherscan.io", "kovan.etherscan.io", "rinkeby.etherscan.io",
               "goerli.etherscan.io", "beacon.etherscan.io", "ftmscan.com", "testnet.ftmscan.com",)
type_search = ("repositories", "code", "commits", "issues", "discussions",
               "registrypackages", "marketplace", "topics", "wikis", "users")

# Create CLI interface
parser = ArgumentParser(
    usage="python %(prog)s {0} [-s {1} {2} {3}] [-c {4}]".format(
        formated("website"), formated("limit"), formated("type"),
        formated("comments"), formated("filename")),
    description="Scrapes smart contracts and checks if they have a github repository. "
                "Visit {0}https://github.com/ivandimitrovkyulev/ContractScrapper{1} "
                "for more info.".format(TextFormat.U, TextFormat.END),
    epilog=f"Version - ContractScrapper {software_ver}", )

# Add all the neccessary CLI arguments
parser.add_argument("website", action="store", type=str, choices=web_choices,
                    metavar=formated("website"),
                    help="Select from the following options: {}".format(web_choices))

parser.add_argument("-s", action=CustomAction, type=str, dest="scrape", nargs='*',
                    options=type_search,
                    metavar=formated("limit"),
                    help="Continuously scraping for new verified contracts from {0} and checks if they have a "
                         "Github repository. If something is found it sends a Telegram message with the results to "
                         "a specified chat. Also keeps a .log file with the results. Kill the script to exit.".format(
                        formated("website")))

parser.add_argument("-c", action="store", type=str, dest="contracts",
                    metavar=formated("filename"),
                    help="Gets all the currently available verified contracts from the {0}website{1} "
                         "and saves them to {0}filename{1}.csv".format(TextFormat.U, TextFormat.END))

parser.add_argument("-l", action="store", type=str, dest="search_code", nargs=3,
                    metavar=(formated("filename"), formated("keyword"), formated("limit")),
                    help="Searches smart contract which contain {0}keyword{1} in their code from the {0}website{1} "
                         "and saves them to {0}filename{1}.csv, {0}limit{1} "
                         "number of maximum returns.".format(TextFormat.U, TextFormat.END))

parser.add_argument("-V", "--version", action="version", version=software_ver,
                    help="Prints the current version of the script.")

# Parse the .env file and load its variables
load_dotenv()

# Name of website to be scrapped
args = parser.parse_args()
web_url = args.website
program_name = os.path.basename(__file__)
program_dir = os.path.dirname(__file__)
web_name = re.sub("\.", "-", web_url)

# Configure logging settings for the Application
logging.basicConfig(filename=f"log_files/{web_name}.log", filemode='a',
                    format='%(asctime)s - %(message)s',
                    level=logging.INFO, datefmt='%Y/%m/%d %H:%M:%S')

contract_cols = ["Link to Contract", "Address", "Contract Name", "Compiler", "Version",
                 "Balance", "Txns", "Setting", "Verified", "Audited", "License"]

# If website argument provided, load driver
if args.website and (args.contracts or args.scrape or args.search_code):
    # load Chrome driver and minimize window
    driver = Chrome(service=Service(os.getenv('CHROME_LOCATION')))
    driver.minimize_window()

    # Start scraping
    start_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    print("{0} – {1} has started screening https://{2}".format(start_time, program_name, web_url))
else:
    parser.exit(0, "Please provide another argument.")

# If, -c contracts is triggered
if args.contracts:
    filename = args.contracts + ".csv"
    # Optional message to print to terminal
    message = ""

    # Get all verified contracts and export to .csv
    get_all_verified_contracts(driver, website_name=web_url, column_names=contract_cols, filename=filename)

    # Print message before exit
    register(exit_handler_2, driver=driver, filename=filename, program_name=program_name, message=message)

# If -l, search_code is triggered
if args.search_code:
    filename = args.search_code[0] + ".csv"
    keyword = args.search_code[1]
    limit = int(args.search_code[2])
    # Optional message to print to terminal
    message = ""

    # Get all verified contracts and export to .csv
    get_all_search_contracts(driver, website_name=web_url, keyword=keyword, max_results=limit, filename=filename)

    # Print message before exit
    register(exit_handler_2, driver=driver, filename=filename, program_name=program_name, message=message)

# If -s, scrape is triggered
if args.scrape:
    # Exit handler function
    register(exit_handler_1, driver=driver, program_name=program_name)

    func_args = []
    try:
        # try to append limit
        func_args.append(args.scrape[0])
        # try to append type
        func_args.append(args.scrape[1])
        # try to append comments
        func_args.append(args.scrape[2])
    except IndexError:
        pass

    print(f"Started logging in log_files/{web_name}.log")

    old_contracts = get_last_n_contracts(driver, web_url)
    while True:
        new_contracts = get_last_n_contracts(driver, web_url)

        # Compare dicts and return new ones
        found_contracts = dict_complement_b(old_contracts, new_contracts)
        for key, value in found_contracts.items():

            # Contract address eg. 0xf7sgf683hf...
            contract_address = re.split(" ", value)[0]
            # Contract name eg. UniswapV3
            contract_name = re.split(" ", value)[1]

            # Search with contract's address first
            search_address = github_search(driver, contract_address, "Solidity", *func_args)

            if search_address is not None:
                # Send telegram message
                message = "\nNew {0} Contract on Github:\n{1}".format(web_url, search_address)
                telegram_send_message(message)
                # Log info
                logging.info([search_address, value])

            else:
                # Then try with contract's name
                search_name = github_search(driver, contract_name, "Solidity", *func_args)

                if search_name is not None:
                    # Send telegram message
                    message = "\nNew {0} Contract on Github:\n{1}".format(web_url, search_name)
                    telegram_send_message(message)
                    # Log info
                    logging.info([search_name, value])

                else:
                    # Log info
                    logging.info([search_name, value])

        # Update Dictionary with latest contracts
        old_contracts = copy.copy(new_contracts)

        # Wait for 30 seconds
        sleep(30)
