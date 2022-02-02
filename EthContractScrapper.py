import re
import os
import sys
import copy
import time
import logging
import pandas as pd
from requests import post
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


def exit_handler():
    """This function must only execute before the end of the process."""

    # Make sure driver is closed if any part of the program returns an error
    driver.close()

    end_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    print("{0} – {1} has stopped.".format(end_time, program_name))

    # Print any information to console as required
    print("Driver closed")


def get_contract_info(content):
    """Extracts the information from the HTML table and
    and returns a Pandas DataFrame object."""

    column_names = ["Address", "Contract Name", "Compiler", "Version", "Balance",
                    "Txns", "Setting", "Verified", "Audited", "License"]

    all_contracts = []
    rows = content.find_elements(By.TAG_NAME, "tr")
    for row in rows:

        contract_info = []
        columns = row.find_elements(By.TAG_NAME, "td")
        for col in columns:

            contract_info.append(col.text)

        all_contracts.append(contract_info)

    df = pd.DataFrame(all_contracts, columns=column_names)
    return df


def get_all_contracts(filename="etherscan.csv", wait_time=20):
    """Collects latest verified contracts from etherscan.io and combines
    them into a Pandas DataFrame. It then saves the DataFrame to the
    provided .csv file."""

    driver.get("https://etherscan.io/contractsVerified/1?ps=100")

    pages = []
    while True:
        xpath_content = "/html/body/div[1]/main/div[2]/div[1]/div[2]/div/div/div[2]/table/tbody"
        content = WebDriverWait(driver, wait_time).until(ec.presence_of_element_located(
            (By.XPATH, xpath_content)))

        page_info = get_contract_info(content)
        pages.append(page_info)

        # Go to the next page
        xpath_button = "/html/body/div[1]/main/div[2]/div[1]/div[2]/div/div/form/div[3]/ul/li[4]"
        next_page = WebDriverWait(driver, wait_time).until(ec.presence_of_element_located((By.XPATH, xpath_button)))

        if len(next_page.find_elements(By.TAG_NAME, "a")) == 0:
            break

        next_page.click()

    info = pd.concat(pages, ignore_index=True)
    info.to_csv(filename)

    return info


def driver_exception_handler(wait_time=10):
    """Infinitely re-tries to query website for information until
    website responds."""

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            while True:
                try:
                    value = func(*args, **kwargs)
                except WebDriverException:
                    time.sleep(wait_time)
                    driver.refresh()
                else:
                    break

            return value

        return wrapper

    return decorator


@driver_exception_handler()
def github_search(keyword, link, language="Solidity", wait_time=20):
    """Searches for a project on Github's advanced search page,
    https://github.com/search/advanced, with provided
    keyword for 'Advanced Search' and language for 'Written in this language'.
    If a result is found it sends a Telegram Message and returns the URL."""

    driver.get("https://github.com/search/advanced")

    xpath_advanced_search = "/html/body/div[4]/main/form/div[1]/div/div/div[1]/label/input"
    advanced_search = WebDriverWait(driver, wait_time).until(ec.presence_of_element_located(
        (By.XPATH, xpath_advanced_search)))
    advanced_search.clear()
    advanced_search.send_keys(keyword)

    # Check if language search parameter is required.
    if language != "":
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

    # If no results found return. Code below this line assumes at least 1 result is returned
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
    if number > 5:
        return None

    # Prepare to send a notification on Telegram with the found contract
    message = "\nNew {0} Contract on Github:\n{1}".format(
                link, driver.current_url)
    data = {"chat_id": chat_id, "text": message, "disable_web_page_preview": True}
    # POST request to Telegram
    post(URL, data)

    return driver.current_url


@driver_exception_handler()
def get_last_n_contracts(chain, n=20, wait_time=20):
    """Returns a Python Dictionary with the first n number of
    specified contracts from etherscan's verified contracts page."""

    driver.get("https://{0}/contractsVerified/1?ps=100".format(chain))

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


# Get argument values to run script
try:
    if sys.argv[1] == '0':
        chain_name = "etherscan"
        chain_url = "etherscan.io"
    elif sys.argv[1] == '1':
        chain_name = "ftmscan"
        chain_url = "ftmscan.com"
    else:
        print("Argument must be 0 or 1.")
        sys.exit()
except IndexError:
    print("Must provide a second argument - 0 for etherscan.io, 1 for ftmscan.com")
    sys.exit()

# Start of script
start_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
program_name = os.path.basename(__file__)
print("{0} – {1} has started screening https://{2}.".format(start_time, program_name, chain_url))


# Configure logging settings for the Application
logging.basicConfig(filename='{}.log'.format(chain_name), filemode='a',
                    format='%(asctime)s - %(message)s',
                    level=logging.INFO, datefmt='%Y/%m/%d %H:%M:%S')

# Load Chrome driver from OS from .env file then load webdriver and minimize window.
load_dotenv()
driver = webdriver.Chrome(service=Service(os.getenv('CHROME_LOCATION')))
driver.minimize_window()
# If program halts exit_handler function will get executed last
register(exit_handler)

# Configure settings to send Telegram message
URL = "https://api.telegram.org/bot{}/sendMessage".format(os.getenv('TOKEN'))
chat_id = os.getenv('CHAT_ID')


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

            search_address = github_search(keyword=contract_address, link=chain_url, language="")
            if search_address is None:

                search_name = github_search(keyword=contract_name, link=chain_url)
                # Update the list and log
                logging.info([search_name, found_contract])

            else:
                # Update the list and log
                logging.info([search_address, found_contract])

    # Update Dictionary with latest contracts
    last_contracts = copy.copy(new_contracts)

    # Wait for 30 seconds
    time.sleep(30)
