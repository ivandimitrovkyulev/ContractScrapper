"""
This program scans for Verified Smart Contracts from selected websites.

For more info please refer to https://github.com/ivandimitrovkyulev/ContractScrapper

Open source and free to use.

"""

# Set up program variables

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
CHROME_LOCATION = os.getenv('CHROME_LOCATION')


web_choices = (
    "etherscan.io",
    "ropsten.etherscan.io",
    "kovan.etherscan.io",
    "rinkeby.etherscan.io",
    "goerli.etherscan.io",
    "beacon.etherscan.io",
    "ftmscan.com",
    "testnet.ftmscan.com",
)

type_search = (
    "repositories",
    "code",
    "commits",
    "issues",
    "discussions",
    "registrypackages",
    "marketplace",
    "topics",
    "wikis",
    "users"
)

contract_cols = (
    "Link to Contract",
    "Address",
    "Contract Name",
    "Compiler",
    "Version",
    "Balance",
    "Txns",
    "Setting",
    "Verified",
    "Audited",
    "License"
)
