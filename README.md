# decent-pubsub-onchain
Solidity code for the on-chain component of Decentagram project

## Release Builds

- GitHub action will automatically build releasing smart contracts on every
  version tag
- The latest release build can be found at [Releases](../../releases)

## Build Locally

- Install `nodeenv` using the following command if it's not installed
  - `python3 -m pip install nodeenv`
  - `nodeenv` is used to create a virtual environment for `npm` packages
- run `make` command under project's root directory, and the generated binary
  files can be find under `build` directory
- The `solc` compiler version can be configured in `utils/nodeenv-requirements.txt`
