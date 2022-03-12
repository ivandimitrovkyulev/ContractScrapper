import re
import copy
import logging

from lxml import html
from time import sleep

from typing import (
    List,
    Dict,
    Union,
)
from pandas import (
    DataFrame,
    concat,
)

from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, TimeoutException

from common.exceptions import driver_wait_exception_handler
from common.message import telegram_send_message


def dict_complement_b(
        old_dict: dict,
        new_dict: dict,
) -> Dict[str, str]:
    """Compares dictionary A & B and returns the relative complement of A in B.
    Basically returns all members in B that are not in A as a python dictionary -
    as in Venn's diagrams.

    :param old_dict: dictionary A
    :param new_dict: dictionary B"""

    b_complement = {k: new_dict[k] for k in new_dict if k not in old_dict}

    return b_complement


def html_table_to_df(
        driver: Chrome,
        column_names: List[str],
        web_name: str,
) -> DataFrame:
    """Extracts the information from a HTML table,
    constructs and returns a Pandas DataFrame object of it.

    :param driver: Selenium webdriver object
    :param column_names: A list of column names that matches the HTML table
    :param web_name: Partial name, eg. etherscan.io"""

    # Parse the html, returning a single document/element
    root = html.fromstring(driver.page_source)

    table = []
    # Get all <tr> table elements
    rows = root.xpath('.//table/tbody/tr')
    for row in rows:

        contract = []
        # Append contract url from first <td> of html table
        link = row[0].xpath(".//a/@href")
        contract_url = web_name + link[0]
        contract.append(contract_url)

        # Iterate through <td> elements
        for cell in row:

            # Get text from <td> element
            cell_info = cell.xpath('.//text()')

            # Discard empty elements
            if len(cell_info) == 1:
                contract.append(cell_info[0])
            else:
                contract.append(cell_info[1])

        table.append(contract)

    df = DataFrame(table, columns=column_names)
    return df


def get_all_verified_contracts(
        driver: Chrome,
        website_name: str,
        column_names: List[str],
        filename: str = "contracts.csv",
        wait_time: int = 1,
) -> DataFrame:
    """Collects latest verified contracts and combines
    them into a Pandas DataFrame object and exports it to
    a specified .csv file.

    :param driver: Selenium webdriver object
    :param website_name: Partial name of website eg. etherscan.io
    :param column_names: List of column names to use in DataFrame construction
    :param filename: Name of file where data will be saved
    :param wait_time: Max seconds to wait for a WebElement"""

    url = "https://{0}/contractsVerified/{1}?ps=100".format(website_name, 1)
    driver.get(url)

    pages = []
    # Iterate through all the web pages
    while True:

        # Construct DataFrame with each HTML table and save in list
        page_info = html_table_to_df(driver, column_names, website_name)
        pages.append(page_info)

        # Go to the next page
        try:
            next_page = WebDriverWait(driver, wait_time).until(ec.presence_of_element_located(
                (By.PARTIAL_LINK_TEXT, "Next")))
            next_page.click()

        except WebDriverException:
            break

    info = concat(pages, ignore_index=True)
    info.to_csv(filename, mode='a', index=False)

    return info


def search_contracts_to_df(
        driver: Chrome,
        web_name: str,
        max_results: int = 20,
) -> DataFrame:
    """Searches for smart contracts from website, eg. etherscan.io, with a given keyword that
    is contained in the solidity code. Returns a DataFrame with matching contracts.

    :param driver: Selenium Webdriver object with a specified get('url') method
    :param web_name: Partial name, eg. etherscan.io
    :param max_results: Maximum number of contracts returned"""

    columns = ["Link to Contract", "Contract Address", "Contract Name", "Date Published", "Transactions"]

    # Get URL's page source
    root = html.fromstring(driver.page_source)

    table = []
    # Get all contract data from current page
    for index, contract in enumerate(root.find_class("card-body p-4")):

        if index >= max_results:
            break

        contract_info = []
        identity = contract.find_class("text-truncate text-primary")[0]

        # Construct the link for the to the contract address
        partial_link = identity.xpath('.//@href')[0]
        contract_link = "https://{0}{1}".format(web_name, partial_link)
        contract_info.append(contract_link)

        # add Contract address to list
        address = identity.xpath('.//text()')[0]
        contract_info.append(address)

        elements = contract.xpath('.//div[2]/div/span')
        try:
            # Append name
            contract_info.append(elements[0].text_content())
            # Append date
            contract_info.append(elements[1].text_content())

            index = len(elements) - 1
            txn = elements[index].text_content()
            regex = re.compile(" ")
            if "txn" in txn:
                transaction = regex.split(txn)[1]
                contract_info.append(transaction)
            else:
                contract_info.append("None")

            # Append contract with its info to table
            table.append(contract_info)
        except IndexError:
            continue

    df = DataFrame(table, columns=columns)
    return df


def get_all_search_contracts(
        driver: Chrome,
        website_name: str,
        filename: str,
        keyword: str,
        max_results: int = 20,
        wait_time: int = 5,
) -> DataFrame:
    """Searches for smart contract code that contains the keyword provided
    and combines them into a Pandas DataFrame object, which is exported to
    a specified .csv file.

    :param driver: Selenium webdriver object
    :param website_name: Partial name of website eg. etherscan.io
    :param filename: Name of file where data will be saved
    :param keyword: Keyword that is contained in the smart contract code
    :param max_results: Maximum number of contracts returned
    :param wait_time: Max seconds to wait for a WebElement"""

    if filename.split(".")[-1] == "csv":
        pass
    else:
        filename += ".csv"

    max_results = int(max_results)

    # Construct a POST request URL
    url = "https://{0}/searchcontractlist?q={1}&a=all&ps=100".format(website_name, keyword)
    driver.get(url)

    pages = []
    # Iterate through all the web pages
    while True:

        # Construct DataFrame with each HTML table and save in list
        page_info = search_contracts_to_df(driver, website_name, max_results)
        pages.append(page_info)

        # Go to the next page
        try:
            next_page = WebDriverWait(driver, wait_time).until(ec.presence_of_element_located(
                (By.PARTIAL_LINK_TEXT, "Next")))
            next_page.click()

        except WebDriverException:
            break

    info = concat(pages, ignore_index=True)
    info.to_csv(filename, mode='a', index=False)

    return info


@driver_wait_exception_handler()
def get_last_n_contracts(
        driver: Chrome,
        website: str,
        n: int = 15,
        wait_time: int = 20,
) -> Dict[str, str]:
    """Returns a Python Dictionary with the first n number of specified contracts
    from the verified contracts page.

    :param driver: Selenium Webdriver object
    :param website: Website URL
    :param n: Number of contracts to be searching at a time
    :param wait_time: Max seconds to wait"""

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


def github_search(
        driver: Chrome,
        keyword: str,
        lang: str = "Solidity",
        limit: str = 7,
        type_search: str = "repositories",
        comments: str = 0,
        wait_time: int = 3,
) -> Union[str, None]:
    """Searches for a project on Github's advanced search page,
    https://github.com/search/advanced.

    :param driver: Selenium webdriver object
    :param keyword: Text to search with in the 'Advanced Search' field
    :param lang: Programming language to be written in
    :param limit: Searches with more returned results will be discarded
    :param type_search: what to search for, eg. repositories, code, commits, etc.
    :param comments: Max comments on repository
    :param wait_time: Max seconds to wait for WebElement"""

    if lang != "":
        lang = lang.lower()
        lang = lang[0].upper() + lang[1:]

    # Construct query URL
    url = "https://github.com/search?q={0}+language:{1}+comments:{2}&type={3}".format(
        keyword, lang, comments, type_search)
    driver.get(url)

    while True:
        try:
            # Number of repositories returned by the search
            css_search_result = "#js-pjax-container > div > div.col-12.col-md-9.float-left.px-2." \
                                "pt-3.pt-md-0.codesearch-results > div > div > h3"
            result_number = WebDriverWait(driver, wait_time).until(ec.presence_of_element_located(
                (By.CSS_SELECTOR, css_search_result)))
        except TimeoutException:
            sleep(5)
            driver.refresh()
        else:
            break

    # If no results return None
    if "We couldn’t find any" in result_number.text:
        return None

    # Check if search returns more results than required
    regex = re.compile("([0-9,.]+)")
    number = regex.findall(result_number.text)[0]
    number = int(re.sub(",", "", number))
    if int(number) > int(limit):
        return None

    # if a result is found - return the url of the results' list
    return driver.current_url


def contract_scraping(
        driver: Chrome,
        web_url: str,
        arguments: List,
):
    """
    Continuously scrapes contracts and checks for a github repo. If a match, that satisfies the
    search criteria, is found it sends a Telegram message to a specified chat. Also keeps a .log
    file with the results.

    :param driver: Selenium web driver object
    :param web_url: String of the url being scrapped
    :param arguments: A list of arguments to be processed
    """

    web_name = re.sub(r"\.", "-", web_url)
    # try to append website, limit, type & comments

    # Configure logging settings for the Application
    logging.basicConfig(filename=f"log_files/{web_name}.log", filemode='a',
                        format='%(asctime)s - %(message)s',
                        level=logging.INFO, datefmt='%Y/%m/%d %H:%M:%S')

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
            search_address = github_search(driver, contract_address, "Solidity", *arguments)

            if search_address is not None:
                # Send telegram message
                message = "\nNew {0} Contract on Github:\n{1}".format(web_url, search_address)
                telegram_send_message(message)
                # Log info
                logging.info([search_address, value])

            else:
                # Then try with contract's name
                search_name = github_search(driver, contract_name, "Solidity", *arguments)

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
