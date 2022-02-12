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
    exit_handler,
    get_all_contracts,
    github_search,
    telegram_send_message,
    get_last_n_contracts,
    CustomAction,
    formated,

)


# Set up arguments, values and settings for CLI interface
software_ver = "1.0.0"
web_choices = ("eth", "eth-test", "ftm", "ftm-test")

parser = ArgumentParser(
    usage="python %(prog)s [-s {0} {1}] [-c {0} {2}]".format(
        formated("website", 'U'), formated("search limit", 'U'), formated("filename", 'U')),
    description="Scrapes smart contracts and checks if they have a github repository. "
                "Visit https://github.com/ivandimitrovkyulev/ContractScrapper for more info.",
    epilog=f"ContractScrapper {software_ver}",)

parser.version = software_ver

parser.add_argument("-s", action=CustomAction, type=str, dest="scrape", nargs=2, options=web_choices,
                    metavar=(formated("website", 'U'), formated("search limit", 'U')),
                    help="Continuously scraping for new verified contracts from the website and checks if they have a "
                         "Github repository. If successful, sends a Telegram message with the results to a specified "
                         "chat. Also keeps a .log file with the results. Kill the script to exit.",
                    )

parser.add_argument("-c", action=CustomAction, type=str, dest="contracts", nargs=2, options=web_choices,
                    metavar=(formated("website", 'U'), formated("filename", 'U')),
                    help="Gets all the currently available verified contracts from the website "
                         "and saves them to filename.csv")

parser.add_argument("-V", "--version", action="version",
                    help="Prints the current version.")

args = parser.parse_args()

# Parse the .env file and load its variables
load_dotenv()
# load Chrome driver
driver = Chrome(service=Service(os.getenv('CHROME_LOCATION')))
driver.minimize_window()
# exit_handler will be the last executed function before program halts
program_name = os.path.basename(__file__)
register(exit_handler(program_name))

if args.scrape:
    web_url = 0
    web_name = 0


# Start of script
start_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
print("{0} – {1} has started screening https://{2}.".format(start_time, program_name, web_url))

contract_columns = ["Address", "Contract Name", "Compiler", "Version", "Balance",
                    "Txns", "Setting", "Verified", "Audited", "License"]

# Configure logging settings for the Application
logging.basicConfig(filename='{}.log'.format(web_name), filemode='a',
                    format='%(asctime)s - %(message)s',
                    level=logging.INFO, datefmt='%Y/%m/%d %H:%M:%S')


# Main While loop to listen for new projects every n secs
last_contracts = get_last_n_contracts(driver, web_url)
while True:
    new_contracts = get_last_n_contracts(driver, web_url)

    # Check for any new contracts. If found search them on Github
    for item in new_contracts:

        # If a new contract is found
        if item not in last_contracts:
            # Get the new contract's info
            found_contract = new_contracts[item]
            found_contract_info = re.split(" ", found_contract)

            # Contract address eg. 0xf7sgf683hf...
            contract_address = found_contract_info[0]
            # Contract name eg. UniswapV3
            contract_name = found_contract_info[1]

            search_address = github_search(keyword=contract_address, link=web_url)
            if search_address is None:

                search_name = github_search(keyword=contract_name, link=web_url, language="Solidity")
                if search_name is str:
                    message = "\nNew {0} Contract on Github:\n{1}".format(
                                web_url, search_name)
                    # send telegram message and log info
                    telegram_send_message(message)
                    logging.info([search_name, found_contract])

            else:
                message = "\nNew {0} Contract on Github:\n{1}".format(
                            web_url, search_address)
                # send telegram message and log info
                telegram_send_message(message)
                logging.info([search_address, found_contract])

    # Update Dictionary with latest contracts
    last_contracts = copy.copy(new_contracts)

    # Wait for 30 seconds
    sleep(30)
