from time import sleep
from functools import wraps
from datetime import datetime

from typing import (
    Callable,
    TypeVar
)

from selenium.webdriver import Chrome
from selenium.common.exceptions import WebDriverException, TimeoutException


# Define a Function type
Function = TypeVar("Function")


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

    print("{0} - {1} has stopped.".format(end_time, program_name))
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
