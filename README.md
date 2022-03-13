# Ethereum Contract Scrapper v2.0.1
Scans for new Verified Solidity Smart Contracts from selected websites and
checks whether they have repos on Github. Searches either with contract address or contract name.
If a contract is found on Github, based on search parameters, a notification with the repo link is sent to a specified Telegram chat.
The script saves all the found contracts in a .log file inside the working directory.
#

## Installation
<br/>

This project uses **Python 3.8.8** and requires a
[Chromium WebDriver](https://chromedriver.chromium.org/getting-started/) installed.

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

You will also need to save the following variables in a **.env** file in ../ContractScrapper/common/:
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

<h2>Examples:</h2>

<ol>
<li> Get the latest available verified contracts from selected website and save them in a **.csv** file:

```
python EthContractScrapper.py -c etherscan.io ether_contracts
```
, where **-c** argument for contracts, **etherscan.io** is website to scrape,  **ether_contracts** is the name of the .csv file to save results into. </li>

<br/>

<li> For continuous scraping of selected website:

```
python EthContractScrapper.py -s ropsten.etherscan.io 7 repositories 5 
```
, where **-s** argument for scraping, **ropsten.etherscan.io** is website to scrape,  **7** is the github search limit beyond which the script does not return results, look for **repositories** in github and repos with **5** minimum comments. Continuously saves the results in **../ContractScrapper/log_files/ropsten-etherscan-io.log** and if a matching result found, sends a message to a specified Telegram chat with a link to the Github repo. </li>

<br/>

<li> Search smart contracts with a keyword that is present in their solidity code:

```
python EthContractScrapper.py -l etherscan.io ether_contracts safemath 30
```
, where **-l** argument for scraping, **etherscan.io** is website to scrape, **ether_contracts** is the filename to save results into, **safemath** keyword to be present in the .sol code, **30** maximum number of results to be saved. </li>

<br/>

<li> For continuous scraping of selected website:

```
python EthContractScrapper.py -ms "etherscan.io ftmscan.com" 5 repositories 10 
```
, where **-ms** argument for scraping, **"etherscan.io ftmscan.com"** are websites to scrape delimited with whitespace,  **5** is the github search limit beyond which the script does not return results, look for **repositories** in github and repos with **10** minimum comments. Continuously saves the results in **../ContractScrapper/log_files/etherscan-io.log** and **../ContractScrapper/log_files/ftmscan-com.log**. If a matching result found, sends a message to a specified Telegram chat with a link to the Github repo. </li>
</ol>

<br/>

Email: ivandkyulev@gmail.com