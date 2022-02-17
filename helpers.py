import re
import os
from argparse import (
    Action,
    ArgumentParser,
)
from lxml import html
from time import sleep
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv
from typing import (
    List,
    Dict,
    Union,
    Callable,
    TypeVar,
    Optional,
)
from requests import (
    post,
    Response,
)

from pandas import (
    DataFrame,
    concat,
)
from selenium.webdriver import Chrome
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, TimeoutException


# Define a Function type
Function = TypeVar("Function")


class TextFormat:
    """Class that implements different text formatting styles."""

    B = '\033[1m'  # Bold
    U = '\033[4m'  # Underline
    IT = '\x1B[3m'  # Italic
    RED = '\033[91m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    END = '\033[0m'  # Every style must have an 'END' at the end


def formated(
        text: str,
        style: str = 'U',
) -> str:
    """Re formats the Text with the specified style.
    Defaults to bold.

    :param text: text to be formatted
    :param style: the style to re-format to, eg. bold, underline, etc. All available options can be
    found in the TextFormat class using the dot operator"""

    # get a list of all available styles
    style_keys = [i for i in TextFormat.__dict__.keys() if i[0] != '_']

    # make sure selected style is available
    assert style in style_keys, "Style not available, please choose from {}".format(style_keys)

    styled_text = "{0}{1}{2}".format(TextFormat.__dict__[style], text, TextFormat.END)

    return styled_text


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


class CustomAction(Action):
    def __init__(self, options, *args, **kwargs):
        self.options = options
        super(CustomAction, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):

        if len(values) > 3:
            ArgumentParser().error(
                message="argument {0}: {1} arguments provided, expected max {2}".format(
                    option_string, len(values), 3))

        try:
            if int(values[0]) >= 0:
                setattr(namespace, self.dest, values)
            else:
                ArgumentParser().error(
                    message="argument {0}: invalid choice: '{1}', choose value >= 0".format(
                        option_string, values[0]))

            if values[1] in self.options:
                setattr(namespace, self.dest, values)
            else:
                ArgumentParser().error(
                    message="argument {0}: invalid choice: '{1}', choose from {2}".format(
                        option_string, values[1], self.options))

            if int(values[2]) >= 0:
                setattr(namespace, self.dest, values)
            else:
                ArgumentParser().error(
                    message="argument {0}: invalid choice: '{1}', choose value >= 0".format(
                        option_string, values[2]))
        except IndexError:
            pass


def exit_handler_1(
        driver: Chrome,
        program_name: str = "Program",
        message: str = "",
) -> None:
    """This function will only execute before the end of the process.

    :param driver: Selenium webdriver object
    :param program_name: Program name
    :param message: Optional message to include"""

    # Make sure driver is closed if any part of the program returns an error
    driver.close()

    # Timestamp of when the program terminated
    end_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')

    # Print any information to console as required
    print("{0} – {1} has stopped.".format(end_time, program_name))
    print(message)
    print("Driver closed.")


def exit_handler_2(
        driver: Chrome,
        filename: str,
        program_name: str = "Program",
        message: str = "",
) -> None:
    """This function will only execute before the end of the process.

    :param driver: Selenium webdriver object
    :param filename: File name
    :param program_name: Program name
    :param message: Optional message to include"""

    # Make sure driver is closed if any part of the program returns an error
    driver.close()

    # Timestamp of when the program terminated
    end_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')

    print("{0} - {1} has stopped.".format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), program_name))
    print(message)
    print("Driver closed.")
    print("Contracts saved to {}".format(filename))


def driver_wait_exception_handler(
        wait_time: int = 10,
) -> Callable[[Function], Function]:
    """ Decorator that infinitely re-tries to query website for information until
    the website responds. Useful when websites enforce a query limit.

    :param wait_time: Seconds to wait until refreshes pages and tries again"""

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            while True:
                try:
                    value = func(*args, **kwargs)

                except WebDriverException or TimeoutException:
                    # if unable to get WebElement - wait & repeat
                    sleep(wait_time)

                else:
                    # if able to retrieve WebElement break loop
                    break

            return value

        return wrapper

    return decorator


def html_table_to_df(
        driver: Chrome,
        column_names: List[str],
        web_name: str,
) -> DataFrame:
    """Extracts the information from a HTML table,
    constructs and returns a Pandas DataFrame object of it.

    :param driver: Selenium webdriver object with a specified get('url') method
    :param column_names: A list of column names that matches the HTML table
    :param web_name: Partial name, eg. etherscan.io"""

    # Parse th html, returning a single document/element
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

    url = "https://{0}/contractsVerified/1?ps=100".format(website_name)
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

        if index > max_results:
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
        keyword: str,
        max_results: int = 20,
        filename: str = "contracts.csv",
        wait_time: int = 5,
) -> DataFrame:
    """Searches for smart contract code that contains the keyword provided
    and combines them into a Pandas DataFrame object, which is exported to
    a specified .csv file.

    :param driver: Selenium webdriver object
    :param website_name: Partial name of website eg. etherscan.io
    :param keyword: Keyword that is contained in the smart contract code
    :param max_results: Maximum number of contracts returned
    :param filename: Name of file where data will be saved
    :param wait_time: Max seconds to wait for a WebElement"""

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


def telegram_send_message(
        message_text: str,
        disable_web_page_preview: bool = True,
        telegram_token: Optional[str] = "",
        telegram_chat_id: Optional[str] = "",
) -> Response:
    r"""Sends a Telegram message to a specified chat.
    Must have a .env file with the following variables:
    TOKEN: your Telegram access token.
    CHAT_ID: the specific id of the chat you want the message sent to
    Follow telegram's instruction of how to set up a bot using the bot father
    and configure it to be able to send messages to a chat.

    :param message_text: Text to be sent to the chat
    :param disable_web_page_preview: Set web preview on/off
    :param telegram_token: Telegram TOKEN API, default take from .env
    :param telegram_chat_id: Telegram chat ID, default take from .env"""

    # if URL not provided - try TOKEN variable from the .env file
    load_dotenv()
    if telegram_token == "":
        telegram_token = str(os.getenv('TOKEN'))

    # if chat_id not provided - try CHAT_ID variable from the .env file
    if telegram_chat_id == "":
        telegram_chat_id = str(os.getenv('CHAT_ID'))

    # construct url using token for a sendMessage POST request
    url = "https://api.telegram.org/bot{}/sendMessage".format(telegram_token)

    # Construct data for the request
    data = {"chat_id": telegram_chat_id, "text": message_text,
            "disable_web_page_preview": disable_web_page_preview}

    # send the POST request
    post_request = post(url, data)

    return post_request


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
