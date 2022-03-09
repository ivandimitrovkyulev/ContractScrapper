from typing import Optional

from requests import (
    post,
    Response
)
from common.variables import (
    TOKEN,
    CHAT_ID,
)


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
    if telegram_token == "":
        telegram_token = TOKEN

    # if chat_id not provided - try CHAT_ID variable from the .env file
    if telegram_chat_id == "":
        telegram_chat_id = CHAT_ID

    # construct url using token for a sendMessage POST request
    url = "https://api.telegram.org/bot{}/sendMessage".format(telegram_token)

    # Construct data for the request
    data = {"chat_id": telegram_chat_id, "text": message_text,
            "disable_web_page_preview": disable_web_page_preview}

    # send the POST request
    post_request = post(url, data)

    return post_request
