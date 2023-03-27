# decent-pubsub-onchain
Solidity code for the on-chain component of Decentagram project

# Ganache
## To start Ganache, create new keys, and add keys to keys directory:
```
ganache-cli -a 20 --network-id 1337 --wallet.accountKeysPath [path_to_decent_lib]/decent-pubsub-onchain/eth_accounts/keys.json
```
## Start Ganache with existing keys.json folder existing:
```
ganache-cli -d -a 20 --network-id 1337
```
### Notes
```
-d = deterministic (deterministic private keys for testing)
-a 20 = create 20 accounts
```

# ToDo
1. Add new subscriber ad-hoc (when a new subscriber joins, they should receive the blacklist) 