"""
This program scans for Verified Smart Contracts from selected websites.

For more info please refer to https://github.com/ivandimitrovkyulev/ContractScrapper

Open source and free to use.

"""

import os
import sys
import re

from argparse import ArgumentParser
from atexit import register
from datetime import datetime
from multiprocessing.dummy import Pool

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service

from common import __version__
from common.exceptions import exit_handler

from common.helpers import (
    get_all_verified_contracts,
    get_all_search_contracts,
    contract_scraping
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
          "[-ms {0}websites{1} {0}limit{1} {0}type{1} {0}comments{1}] "
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
    options=(web_choices, type_search), metavar=formatted("websites"),
    help=f"Continuously scraping for new verified contracts from selected {formatted('websites')} and checks "
         f"if they have a Github repository. If something is found it sends a Telegram message with the results to "
         f"a specified chat. Also keeps a .log file with the results. To select multiple {formatted('websites')} "
         f"provide a single string delimited with whitespace, eg. 'etherscan.io ftmscan.com'. Provide "
         f"{formatted('limit')} to limit return results from Github. Parameter {formatted('type')} is for type "
         f"of Github search, eg. repo, users, commits etc. Parameter {formatted('comments')} is for max number of "
         f"comments on repo. Kill the script to exit."
)
parser.add_argument(
    "-s", action=CustomActionScrape, type=str, dest="scrape", nargs='*',
    options=(web_choices, type_search), metavar=formatted("website"),
    help=f"Continuously scraping for new verified contracts from {formatted('website')} and checks if they have a "
         f"Github repository. If something is found it sends a Telegram message with the results to "
         f"a specified chat. Also keeps a .log file with the results. Provide {formatted('limit')} to limit"
         f"return results from Github. Parameter {formatted('type')} is for type of Github search, eg. repo, "
         f"users, commits etc. Parameter {formatted('comments')} is for max number of comments on repo. "
         f"Kill the script to exit."
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

# If website argument provided, load driver
if args.scrape or args.code or args.contracts:
    # load Chrome driver and minimize window
    driver = Chrome(service=Service(CHROME_LOCATION))
    driver.minimize_window()

    # Start scraping
    start_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    print("{0} – {1} has started.".format(start_time, program_name))
elif args.multi_scrape:
    pass
else:
    sys.exit("Please provide at least one additional argument.")


# If -c, trigger contracts
if args.contracts:
    filename = args.contracts[1] + ".csv"
    # Exit handler function with optional message
    message = f"Results saved in {program_dir}/{formatted(filename)}"
    web_url = args.contracts[0]

    # Print message before exit
    register(exit_handler, driver, program_name, message)

    # Get all verified contracts and export to .csv
    get_all_verified_contracts(driver, website_name=web_url, column_names=contract_cols, filename=filename)

# If -l, trigger code
if args.code:
    # Get arguments
    code_args = [x for x in args.code]

    filename = args.code[1]
    # Exit handler function with optional message
    message = f"Results saved in {program_dir}/{formatted(filename)}"
    register(exit_handler, driver, program_name, message)

    # Get all verified contracts and export to .csv
    get_all_search_contracts(driver, *code_args)

# If -s, trigger scrape
if args.scrape:
    web_url, *scrape_args = args.scrape
    web_name = re.sub(r"\.", "-", web_url)

    # Exit handler function with optional message
    message = f"Results saved in {program_dir}/{web_name}.log"
    register(exit_handler, driver, program_name, message)

    contract_scraping(driver, web_url, scrape_args)

# If -ms, trigger multi_scrape
if args.multi_scrape:
    urls, *arguments = args.multi_scrape
    web_urls = [url for url in urls.split(" ")]
    web_names = [re.sub(r"\.", "-", name) for name in web_urls]

    drivers = [Chrome(service=Service(CHROME_LOCATION)) for x in web_names]
    messages = [f"Results saved in {program_dir}/{name}.log" for name in web_names]

    register_args = [(exit_handler, driver, program_dir, message)
                     for driver, message in zip(drivers, messages)]
    scrape_args = [(driver, url, arguments)
                   for driver, url in zip(drivers, web_urls)]

    # Multiprocessing Pool with web_urls number of processes
    with Pool(len(web_urls)) as pool:
        # Exit handler function with optional message
        pool.starmap(register, register_args)

        # Start scraping
        results = pool.starmap(contract_scraping, scrape_args)
