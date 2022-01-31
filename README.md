#Ethereum Contract Scrapper

This script scans Etherscan.io for new verified smart contracts and then
checks whether they are on Github using either contract address or name.
It looks for repos with Solidity code. 
If a contract is found on Github a notification with the repo link is sent
to Telegram's @ContractCodebot (https://t.me/ContractCodebot)

#Installation