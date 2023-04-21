# decent-pubsub-onchain
Solidity code for the on-chain component of Decentagram project

## Release Builds

- GitHub action will automatically build releasing smart contracts on every
  version tag
- The latest release build can be found at [Releases](./releases)

## Build Locally

- Install `nodeenv` using the following command if it's not installed
  - `python3 -m pip install nodeenv`
  - `nodeenv` is used to create a virtual environment for `npm` packages
- run `make` command under project's root directory, and the generated binary
  files can be find under `build` directory
- The `solc` compiler version can be configured in `utils/nodeenv-requirements.txt`

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
