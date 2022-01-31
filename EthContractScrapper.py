import re
import os
import time
import copy
import logging
import telegram_send
import pandas as pd
from functools import wraps
from atexit import register
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException


def exit_handler():
    """This function must only execute before the end of the process."""

    # Make sure driver is closed if any part of the program returns an error
    driver.close()

    end_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    print("{0} – {1} has stopped.".format(end_time, PROGRAM_NAME))

    # Print any information to console as required
    print("Driver closed")


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
        content = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located(
            (By.XPATH, xpath_content)))

        page_info = get_contract_info(content)
        pages.append(page_info)

        # Go to the next page
        xpath_button = "/html/body/div[1]/main/div[2]/div[1]/div[2]/div/div/form/div[3]/ul/li[4]"
        next_page = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.XPATH, xpath_button)))

        if len(next_page.find_elements(By.TAG_NAME, "a")) == 0:
            break

        next_page.click()

    info = pd.concat(pages, ignore_index=True)
    info.to_csv(filename)

    return info


@driver_exception_handler()
def github_search(keyword, language="Solidity", wait_time=20):
    """Searches for a contract on Github's advanced search page,
    https://github.com/search/advanced, with provided
    keyword for 'Advanced Search' and language for 'Written in this language'.
    if a result is found it sends a Telegram Message and returns the URL."""

    driver.get("https://github.com/search/advanced")

    xpath_advanced_search = "/html/body/div[4]/main/form/div[1]/div/div/div[1]/label/input"
    advanced_search = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located(
        (By.XPATH, xpath_advanced_search)))
    advanced_search.clear()
    advanced_search.send_keys(keyword)

    # Check if language search parameter is required.
    if language != "":
        xpath_language = "/html/body/div[4]/main/form/div[2]/fieldset[1]/dl[4]/dd/select"
        select_language = Select(WebDriverWait(driver, wait_time).until(EC.presence_of_element_located(
            (By.XPATH, xpath_language))))
        select_language.select_by_visible_text(language)

    xpath_button = "/html/body/div[4]/main/form/div[1]/div/div/div[2]/button"
    WebDriverWait(driver, wait_time).until(EC.presence_of_element_located(
        (By.XPATH, xpath_button))).click()

    xpath_result = "//*[@id='js-pjax-container']/div/div[3]/div/div/h3"
    result = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located(
        (By.XPATH, xpath_result)))

    if "We couldn’t find any" in result.text:
        return "No code in Github."

    else:
        message = "\nNew Contract found on Github:\n{0}".format(driver.current_url)
        # send the found contract to Telegram to notify
        telegram_send.send(messages=[message])

        return driver.current_url


@driver_exception_handler()
def get_last_n_contracts(n=20, wait_time=20):
    """Returns a Python Dictionary with the first n number of
    specified contracts from etherscan's verified contracts page."""

    xpath_content = "/html/body/div[1]/main/div[2]/div[1]/div[2]/div/div/div[2]/table/tbody"
    driver.get("https://etherscan.io/contractsVerified/1?ps=100")
    content = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located(
        (By.XPATH, xpath_content)))

    rows = content.find_elements(By.TAG_NAME, "tr")
    return_dict = {}
    for number in range(n):
        # Add tr[i] item from the HTML Table
        row = rows[number].text
        key = re.split(" ", row)[0]
        return_dict[key] = row

    return return_dict


# Start of script
start_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
PROGRAM_NAME = os.path.basename(__file__)
print("{0} – {1} has started.".format(start_time, PROGRAM_NAME))

# Configure logging settings for the Application
logging.basicConfig(filename='app.log', filemode='a',
                    format='%(asctime)s - %(message)s',
                    level=logging.INFO, datefmt='%Y/%m/%d %H:%M:%S')

# Load Chrome driver from OS from .env file then load webdriver and minimize window.
load_dotenv()
driver = webdriver.Chrome(service=Service(os.getenv('CHROME_LOCATION')))
driver.minimize_window()
# If program halts exit_handler function will get executed last
register(exit_handler)


# Main While loop to listen for new projects every n secs
last_contracts = get_last_n_contracts()
while True:
    new_contracts = get_last_n_contracts()

    # Check for any new contracts
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

            search_address = github_search(keyword=contract_address, language="")
            if type(search_address) is str:

                search_name = github_search(keyword=contract_name)
                if type(search_name) is not str:
                    # If contract found in Github update the list and log
                    logging.info([search_name, found_contract])

            else:
                # If contract found in Github update the list and log
                logging.info([search_address, found_contract])

    # Update Dictionary with latest contracts
    last_contracts = copy.copy(new_contracts)

    # Wait for 30 seconds
    time.sleep(30)
