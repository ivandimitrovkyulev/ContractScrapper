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

import re
import os
import copy
import time
import logging
import argparse
from typing import Callable
import pandas as pd
from requests import post, Response
from functools import wraps
from atexit import register
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webelement import WebElement


def exit_handler(
        name: str = "Program",
) -> None:
    """This function will only execute before the end of the process.
    name: Program name"""

    # Make sure driver is closed if any part of the program returns an error
    driver.close()

    # Timestamp of when the program terminated
    end_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')

    # Print any information to console as required
    print("{0} – {1} has stopped.".format(end_time, name))
    print("Driver closed.")


def html_table_to_df(
        content: WebElement,
        column_names: list,
) -> pd.DataFrame:
    """Extracts the information from a HTML table,
    constructs and returns a Pandas DataFrame object of it.

    content: a Selenium WebElement that is a HTML Table
    column_names: A list of column names that matches the HTML table"""

    # All contracts
    all_contracts = []
    # Iterate all contracts
    rows = content.find_elements(By.TAG_NAME, "tr")
    for row in rows:

        # All info of a single contract
        contract_info = []
        # Iterate all info in a contract
        columns = row.find_elements(By.TAG_NAME, "td")
        for col in columns:

            contract_info.append(col.text)

        all_contracts.append(contract_info)

    df = pd.DataFrame(all_contracts, columns=column_names)
    return df


def get_all_contracts(
        website: str,
        filename: str = "contracts.csv",
        wait_time: int = 20,
        column_names=None,
) -> pd.DataFrame:
    """Collects latest verified contracts and combines
    them into a Pandas DataFrame object and exports it to
    a specified .csv file.

    filename: name of file where data will be saved
    wait_time: maximum no. of seconds to wait for a WebElement
    column_names: list of column names for the pandas DataFrame object"""

    url = "https://{}/contractsVerified/1?ps=100".format(website)
    driver.get(url)

    pages = []
    # Iterate through all the web pages
    while True:
        xpath_content = "/html/body/div[1]/main/div[2]/div[1]/div[2]/div/div/div[2]/table/tbody"
        content = WebDriverWait(driver, wait_time).until(ec.presence_of_element_located(
            (By.XPATH, xpath_content)))

        page_info = html_table_to_df(content, column_names)
        pages.append(page_info)

        # Go to the next page
        xpath_button = "/html/body/div[1]/main/div[2]/div[1]/div[2]/div/div/form/div[3]/ul/li[4]"
        next_page = WebDriverWait(driver, wait_time).until(ec.presence_of_element_located(
            (By.XPATH, xpath_button)))

        if len(next_page.find_elements(By.TAG_NAME, "a")) == 0:
            break

        next_page.click()

    info = pd.concat(pages, ignore_index=True)
    info.to_csv(filename)

    return info


def driver_wait_exception_handler(
        wait_time: int = 10,
) -> Callable[[f], f]:
    """ Decorator that infinitely re-tries to query website for information until
    the website responds. Useful when websites enforce a query limit.

    wait_time: No. of seconds to wait until refreshes pages and tries again"""

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            while True:
                try:
                    value = func(*args, **kwargs)

                except WebDriverException:
                    # if unable to get WebElement - wait, refresh & repeat
                    time.sleep(wait_time)
                    driver.refresh()

                else:
                    # if able to retrieve WebElement break loop
                    break

            return value

        return wrapper

    return decorator


@driver_wait_exception_handler()
def github_search(
        keyword: str,
        language: str,
        wait_time: int = 20,
        max_results: int = 5,
) -> str or None:
    """Searches for a project on Github's advanced search page,
    https://github.com/search/advanced.

    keyword: text to search with in the 'Advanced Search' field
    language: programming language to be written in
    wait_time: max no. of seconds to wait for WebElement
    max_results: searches with more returned results will be discarded"""

    driver.get("https://github.com/search/advanced")

    xpath_advanced_search = "/html/body/div[4]/main/form/div[1]/div/div/div[1]/label/input"
    advanced_search = WebDriverWait(driver, wait_time).until(ec.presence_of_element_located(
        (By.XPATH, xpath_advanced_search)))
    advanced_search.clear()
    advanced_search.send_keys(keyword)

    # Check if language search parameter is required.
    if language != "":
        language = language.lower()
        language = language[0].upper() + language[1:]
        xpath_language = "/html/body/div[4]/main/form/div[2]/fieldset[1]/dl[4]/dd/select"
        select_language = Select(WebDriverWait(driver, wait_time).until(ec.presence_of_element_located(
            (By.XPATH, xpath_language))))
        select_language.select_by_visible_text(language)

    xpath_button = "/html/body/div[4]/main/form/div[1]/div/div/div[2]/button"
    WebDriverWait(driver, wait_time).until(ec.presence_of_element_located(
        (By.XPATH, xpath_button))).click()

    xpath_result = "//*[@id='js-pjax-container']/div/div[3]/div/div/h3"
    result = WebDriverWait(driver, wait_time).until(ec.presence_of_element_located(
        (By.XPATH, xpath_result)))

    # If no results found return None. Code below this line assumes at least 1 result is returned
    if "We couldn’t find any" in result.text:
        return None

    # Check for how many repository results the search returned
    classname_result_number = "#js-pjax-container > div > div.col-12.col-md-9.float-left.px-2.pt-3.pt-md-0" \
                              ".codesearch-results > div > div.d-flex.flex-column.flex-md-row.flex-justify-between" \
                              ".border-bottom.pb-3.position-relative"
    result_number = WebDriverWait(driver, wait_time).until(ec.presence_of_element_located(
        (By.CSS_SELECTOR, classname_result_number)))
    regex = re.compile("([0-9,.]+)")
    number = regex.findall(result_number.text)[0]
    number = int(re.sub(",", "", number))

    # Check if search returns more results than required
    if number > max_results:
        return None

    # if a result is found - return the github results' list url
    return driver.current_url


def telegram_send_message(
        message_text: str,
        disable_web_page_preview: bool = True,
        telegram_token: str = "",
        telegram_chat_id: str = "",
) -> Response:
    """Sends a Telegram message to a specified chat.
    Must have a .env file with the following variables:
    TOKEN: your Telegram access token.
    CHAT_ID: the specific id of the chat you want the message sent to
    Follow telegram's instruction of how to set up a bot using the bot father
    and configure it to be able to send messages to a chat.

    message: Text to be sent to the chat
    disable_web_page_preview: Set web preview on/off
    telegram_token: Telegram TOKEN API
    telegram_chat_id: Telegram chat ID"""

    # if URL not provided try TOKEN variable from a .env file
    load_dotenv()
    if telegram_token == "":
        telegram_token = os.getenv('TOKEN')

    # if chat_id not provided try CHAT_ID variable from a .env file
    if telegram_chat_id == "":
        telegram_chat_id = os.getenv('CHAT_ID')

    # construct url using token for a sendMessage POST request
    url = "https://api.telegram.org/bot{}/sendMessage".format(telegram_token)

    # Construct data for the request
    data = {"chat_id": telegram_chat_id, "text": message_text,
            "disable_web_page_preview": disable_web_page_preview}

    # send the POST request
    response = post(url, data)

    return response


@driver_wait_exception_handler()
def get_last_n_contracts(
        website: str,
        n: int = 20,
        wait_time: int = 20,
) -> dict:
    """Returns a Python Dictionary with the first n number of
    specified contracts from the verified contracts page."""

    url = "https://{0}/contractsVerified/1?ps=100".format(website)
    driver.get(url)

    xpath_content = "/html/body/div[1]/main/div[2]/div[1]/div[2]/div/div/div[2]/table/tbody"
    content = WebDriverWait(driver, wait_time).until(ec.presence_of_element_located(
        (By.XPATH, xpath_content)))

    rows = content.find_elements(By.TAG_NAME, "tr")
    return_dict = {}
    for number in range(n):
        # Add tr[i] item from the HTML Table
        row = rows[number].text
        key = re.split(" ", row)[0]
        return_dict[key] = row

    return return_dict


# Get and check argument values to run the script
CLI = argparse.ArgumentParser()
CLI.add_argument("argument", type=str)
arg = CLI.parse_args()

if arg.argument.lower() == "eth":
    chain_name = "etherscan"
    chain_url = "etherscan.io"
elif arg.argument.lower() == "ftm":
    chain_name = "ftmscan"
    chain_url = "ftmscan.com"
else:
    CLI.exit(message="Must provide the correct argument - eth for etherscan.io, ftm for ftmscan.com")


# Start of script
start_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
program_name = os.path.basename(__file__)
print("{0} – {1} has started screening https://{2}.".format(start_time, program_name, chain_url))

contract_columns = ["Address", "Contract Name", "Compiler", "Version", "Balance",
                    "Txns", "Setting", "Verified", "Audited", "License"]

# Configure logging settings for the Application
logging.basicConfig(filename='{}.log'.format(chain_name), filemode='a',
                    format='%(asctime)s - %(message)s',
                    level=logging.INFO, datefmt='%Y/%m/%d %H:%M:%S')

# Parse the .env file and load its variables
load_dotenv()
# load Chrome driver
driver = webdriver.Chrome(service=Service(os.getenv('CHROME_LOCATION')))
driver.minimize_window()
# exit_handler will be the last executed function before program halts
register(exit_handler(program_name))


# Main While loop to listen for new projects every n secs
last_contracts = get_last_n_contracts(chain_url)
while True:
    new_contracts = get_last_n_contracts(chain_url)

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

            search_address = github_search(keyword=contract_address, link=chain_url)
            if search_address is None:

                search_name = github_search(keyword=contract_name, link=chain_url, language="Solidity")
                if search_name is str:
                    message = "\nNew {0} Contract on Github:\n{1}".format(
                                chain_url, search_name)
                    # send telegram message and log info
                    telegram_send_message(message)
                    logging.info([search_name, found_contract])

            else:
                message = "\nNew {0} Contract on Github:\n{1}".format(
                            chain_url, search_address)
                # send telegram message and log info
                telegram_send_message(message)
                logging.info([search_address, found_contract])

    # Update Dictionary with latest contracts
    last_contracts = copy.copy(new_contracts)

    # Wait for 30 seconds
    time.sleep(30)
