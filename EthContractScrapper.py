"""
This program scans for Verified Smart Contracts from selected websites.

For more info please refer to https://github.com/ivandimitrovkyulev/ContractScrapper

Open source and free to use.

"""

import os
import sys
import re
import logging
import copy

from time import sleep
from argparse import ArgumentParser
from atexit import register
from datetime import datetime

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service

from common import __version__
from common.exceptions import exit_handler
from common.message import telegram_send_message

from common.helpers import (
    github_search,
    get_last_n_contracts,
    get_all_verified_contracts,
    get_all_search_contracts,
    dict_complement_b,
)
from common.format import (
    formatted,
    TextFormat,
)
from common.cli import (
    CustomActionSearch,
    CustomActionScrape,
    CustomActionContracts,
)
from common.variables import (
    CHROME_LOCATION,
    web_choices,
    type_search,
    contract_cols,
)


# Create CLI interface
parser = ArgumentParser(
    usage="python %(prog)s "
          "[-s {0}website{1} {0}limit{1} {0}type{1} {0}comments{1}] "
          "[-ms {0}website{1} {0}limit{1} {0}type{1} {0}comments{1}] "
          "[-c {0}website{1} {0}filename{1}] "
          "[-l {0}website{1} {0}filename{1} {0}keyword{1} {0}limit{1}]".format(
            TextFormat.U, TextFormat.END),
    description="Scrapes smart contracts and checks if they have a github repository. "
                "Visit {0}https://github.com/ivandimitrovkyulev/ContractScrapper{1} "
                "for more info.".format(TextFormat.U, TextFormat.END),
    epilog=f"Version - %(prog)s {__version__}",
)

# Add all the necessary CLI arguments
parser.add_argument(
    "-ms", action=CustomActionScrape, type=str, dest="multi_scrape", nargs='*',
    options=type_search, metavar=formatted("website"),
    help=f"Continuously scraping for new verified contracts from {formatted('website')} and checks if they have a "
         "Github repository. If something is found it sends a Telegram message with the results to "
         "a specified chat. Also keeps a .log file with the results. Kill the script to exit."
)
parser.add_argument(
    "-s", action=CustomActionScrape, type=str, dest="scrape", nargs='*',
    options=type_search, metavar=formatted("website"),
    help=f"Continuously scraping for new verified contracts from {formatted('website')} and checks if they have a "
         "Github repository. If something is found it sends a Telegram message with the results to "
         "a specified chat. Also keeps a .log file with the results. Kill the script to exit."
)
parser.add_argument(
    "-l", action=CustomActionSearch, type=str, dest="code", nargs='*',
    options=web_choices, metavar=formatted("website"),
    help="Searches smart contract which contain {0}keyword{1} in their code from the "
         "{0}website{1} and saves them to {0}filename{1}.csv, {0}limit{1} "
         "number of maximum returns.".format(TextFormat.U, TextFormat.END)
)
parser.add_argument(
    "-c", action=CustomActionContracts, type=str, dest="contracts", nargs=2,
    options=web_choices, metavar=(formatted("website"), formatted("filename")),
    help="Gets all the currently available verified contracts from the {0}website{1} "
         "and saves them to {0}filename{1}.csv".format(TextFormat.U, TextFormat.END)
)
parser.add_argument(
    "-v", "--version", action="version", version=__version__,
    help="Prints the current version of the script."
)

# Name of website to be scrapped
args = parser.parse_args()
program_name = os.path.basename(__file__)
program_dir = os.getcwd()
print(args)

# If website argument provided, load driver
if args.multi_scrape or args.scrape or args.code or args.contracts:
    # load Chrome driver and minimize window
    driver = Chrome(service=Service(CHROME_LOCATION))
    driver.minimize_window()

    # Start scraping
    start_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    print("{0} – {1} has started.".format(start_time, program_name))
else:
    sys.exit("Please provide at least one additional argument.")


# web_url = args.website
# web_name = re.sub("\.", "-", web_url)

# If -c, trigger contracts
if args.contracts:
    filename = args.contracts[1] + ".csv"
    # Optional message to print to terminal
    message = f"Results saved in {program_dir}/{formatted(filename)}"
    web_url = args.contracts[0]

    # Print message before exit
    register(exit_handler, driver=driver, program_name=program_name, message=message)

    # Get all verified contracts and export to .csv
    get_all_verified_contracts(driver, website_name=web_url, column_names=contract_cols, filename=filename)

# If -l, trigger code
if args.code:
    try:
        code_args = [x for x in args.code]
    except IndexError:
        pass
    # Optional message to print to terminal
    filename = args.code[1]
    message = f"Results saved in {program_dir}/{formatted(filename)}"
    # Print message before exit
    register(exit_handler, driver=driver, program_name=program_name, message=message)

    # Get all verified contracts and export to .csv
    get_all_search_contracts(driver, *code_args)

# If -s, trigger scrape
if args.scrape:
    # Optional message to print to terminal
    message = ""
    # Exit handler function
    register(exit_handler, driver=driver, program_name=program_name, message=message)

    # Configure logging settings for the Application
    logging.basicConfig(filename=f"log_files/{web_name}.log", filemode='a',
                        format='%(asctime)s - %(message)s',
                        level=logging.INFO, datefmt='%Y/%m/%d %H:%M:%S')

    # try to append limit, type & comments
    try:
        scrape_args = [x for x in args.scrape]
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
            search_address = github_search(driver, contract_address, "Solidity", *scrape_args)

            if search_address is not None:
                # Send telegram message
                message = "\nNew {0} Contract on Github:\n{1}".format(web_url, search_address)
                telegram_send_message(message)
                # Log info
                logging.info([search_address, value])

            else:
                # Then try with contract's name
                search_name = github_search(driver, contract_name, "Solidity", *scrape_args)

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
