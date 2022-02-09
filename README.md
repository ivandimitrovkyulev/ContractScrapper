# Ethereum Contract Scrapper
This script scans etherscan.io or ftmscan.com for new Verified Smart Contracts and then
checks whether they have repos on Github using either contract address or contract name.
It looks for repossitories written in Solidity. 
If a contract is found on Github a notification with the repo link is sent
to a specified Telegram chat.
The script saves all the found contracts in a **.log** file inside your working directory.
#
## Installation
This project uses **Python 3.8.8** and requires a [Chromium WebDriver](https://chromedriver.chromium.org/getting-started).

Clone the project:
```
git clone https://github.com/ivandimitrovkyulev/ContractScrapper.git
```

```
cd ContractScrapper
```

Create a virtual environment in the current working directory and activate it:

```
python3 -m venv <current-directory>
```
```
source <current-directory>/bin/activate
```

Install all third-party project dependencies:
```
pip install -r requirements.txt
```

You will also need to save the following variables in a **.env** file in the same directory:
```
CHROME_LOCATION=<your-web-driver-path-location> 

TOKEN=<telegram-token-for-your-bot>

CHAT_ID=<the-id-of-your-telegram-chat>
```
#
## Running the script 

For [Etherscan](https://etherscan.io):
```
python3 EthContractScrapper.py 0
```

For [Fantomscan](https://ftmscan.com):

```
python3 EthContractScrapper.py 1
```