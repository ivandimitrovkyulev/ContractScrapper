# Ethereum Contract Scrapper v1.1.0
This script scans for new Verified Solidity Smart Contracts from selected websites and
checks whether they have repos on Github. Searches either with contract address or contract name.
If a contract is found on Github, based on search parameters, a notification with the repo link is sent to a specified Telegram chat.
The script saves all the found contracts in a .log file inside your working directory.
#

## Installation
<br/>
This project uses **Python 3.8.8** and requires a [Chromium WebDriver](https://chromedriver.chromium.org/getting-started).

Clone the project:
```
git clone https://github.com/ivandimitrovkyulev/ContractScrapper.git

cd ContractScrapper
```

Create a virtual environment in the current working directory and activate it:

```
python3 -m venv <current-directory>

source <current/directory>/bin/activate
```

Install all third-party project dependencies:
```
pip install -r requirements.txt
```

You will also need to save the following variables in a **.env** file in the same directory:
```
CHROME_LOCATION=<your/web/driver/path/location> 

TOKEN=<telegram-token-for-your-bot>

CHAT_ID=<the-id-of-your-telegram-chat>
```
<br/>

## Running the script
<br/>

For help using the script:
```
python EthContractScrapper.py -h
```
<br/>

**Example 1**. Get the latest available verified contracts from selected website and save them in a**.csv** file:

```
python EthContractScrapper.py etherscan.io -c contracts
```
, where **etherscan.io** is website to scrape, **-c** argument for contracts, **contracts** is the name of the .csv file.

<br/>

**Example 2.** For continuous scraping of selected website:

```
python EthContractScrapper.py ropsten.etherscan.io -s 7 repositories 5
```
, where **ropsten.etherscan.io** is website to scrape, **-s** argument for scraping, **7** is the github search limit beyond which the script does not return results, look for **repositories** in github and repos with **5** minimum comments. Continuously saves the results in **../ContractScrapper/log_files/ropsten-etherscan-io.log**

<br/>

**Example 3.** Search smart contracts with a keyword that is present in their solidity code:

```
python EthContractScrapper.py etherscan.io -l contracts safemath 30
```
, where **etherscan.io** is website to scrape, **-l** argument for scraping, **contracts** is the filename to save into to, **safemath** keyword to be present in the .sol code, **30** maximum number of results to be saved.

<br/>
Email: ivandkyulev@gmail.com