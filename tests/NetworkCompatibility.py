#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2024 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import argparse
import logging
import os
import random
import time

from web3 import Web3
from PyEthHelper import EthContractHelper
from PyEthHelper import GanacheAccounts


BASE_DIR_PATH       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR_PATH      = os.path.join(BASE_DIR_PATH, 'build')
UTILS_DIR_PATH      = os.path.join(BASE_DIR_PATH, 'utils')
PYHELPER_DIR        = os.path.join(UTILS_DIR_PATH, 'PyEthHelper')
PROJECT_CONFIG_PATH = os.path.join(UTILS_DIR_PATH, 'project_conf.json')
PUBLISH_MSG_GAS_EST = 134745


LOGGER = logging.getLogger('NetworkCompatibility')


def RunTests(apiUrl: str, keyfile: os.PathLike) -> dict:
	# connect to endpoint
	w3 = Web3(Web3.HTTPProvider(apiUrl))
	while not w3.is_connected():
		LOGGER.info('Attempting to connect to endpoint...')
		time.sleep(1)
	LOGGER.info('Connected to endpoint')

	# checksum keys
	GanacheAccounts.ChecksumGanacheKeysFile(
		keyfile,
		keyfile
	)

	# setup account
	privKey = EthContractHelper.SetupSendingAccount(
		w3=w3,
		account=0,
		keyJson=keyfile
	)
	# deploy PubSub contract
	LOGGER.info('Deploying PubSub contract...')
	pubSubContract = EthContractHelper.LoadContract(
		w3=w3,
		projConf=PROJECT_CONFIG_PATH,
		contractName='PubSubService',
		release=None, # use locally built contract
		address=None, # deploy new contract
	)
	pubSubReceipt = EthContractHelper.DeployContract(
		w3=w3,
		contract=pubSubContract,
		arguments=[ ],
		privKey=privKey,
		gas=None, # let web3 estimate
		value=0,
		confirmPrompt=False # don't prompt for confirmation
	)
	pubSubAddr = pubSubReceipt.contractAddress
	LOGGER.info('PubSub contract deployed at {}'.format(pubSubAddr))

	# load deployed PubSub contract
	pubSubContract = EthContractHelper.LoadContract(
		w3=w3,
		projConf=PROJECT_CONFIG_PATH,
		contractName='PubSubService',
		release=None, # use locally built contract
		address=pubSubAddr, # use deployed contract
	)

	##########
	# Publisher and register
	##########

	# deploy Publisher contract
	LOGGER.info('Deploying publisher contract...')
	publisherContract = EthContractHelper.LoadContract(
		w3=w3,
		projConf=PROJECT_CONFIG_PATH,
		contractName='HelloWorldPublisher',
		release=None, # use locally built contract
		address=None, # deploy new contract
	)
	publisherReceipt = EthContractHelper.DeployContract(
		w3=w3,
		contract=publisherContract,
		arguments=[ ],
		privKey=privKey,
		gas=None, # let web3 estimate
		value=0,
		confirmPrompt=False # don't prompt for confirmation
	)
	publisherAddr = publisherReceipt.contractAddress
	LOGGER.info('Publisher contract deployed at {}'.format(publisherAddr))

	# load deployed Publisher contract
	publisherContract = EthContractHelper.LoadContract(
		w3=w3,
		projConf=PROJECT_CONFIG_PATH,
		contractName='HelloWorldPublisher',
		release=None, # use locally built contract
		address=publisherAddr, # use deployed contract
	)

	# register publisher
	LOGGER.info('Registering publisher...')
	regTxReceipt = EthContractHelper.CallContractFunc(
		w3=w3,
		contract=publisherContract,
		funcName='register',
		arguments=[ pubSubAddr ],
		privKey=privKey,
		gas=None, # let web3 estimate
		value=0,
		confirmPrompt=False # don't prompt for confirmation
	)

	##########
	# Subscriber and subscribe
	##########

	# deploy Subscriber contract
	LOGGER.info('Deploying subscriber contract...')
	subscriberContract = EthContractHelper.LoadContract(
		w3=w3,
		projConf=PROJECT_CONFIG_PATH,
		contractName='HelloWorldSubscriber',
		release=None, # use locally built contract
		address=None, # deploy new contract
	)
	subscriberReceipt = EthContractHelper.DeployContract(
		w3=w3,
		contract=subscriberContract,
		arguments=[ pubSubAddr ],
		privKey=privKey,
		gas=None, # let web3 estimate
		value=0,
		confirmPrompt=False # don't prompt for confirmation
	)
	subscriberAddr = subscriberReceipt.contractAddress

	# load deployed Subscriber contract
	subscriberContract = EthContractHelper.LoadContract(
		w3=w3,
		projConf=PROJECT_CONFIG_PATH,
		contractName='HelloWorldSubscriber',
		release=None, # use locally built contract
		address=subscriberAddr, # use deployed contract
	)

	# subscribe
	LOGGER.info('Subscribing...')
	gasPrice = int(subscriberReceipt.effectiveGasPrice)
	depositEst = gasPrice * PUBLISH_MSG_GAS_EST
	subTxReceipt = EthContractHelper.CallContractFunc(
		w3=w3,
		contract=subscriberContract,
		funcName='subscribe',
		arguments=[ publisherAddr ],
		privKey=privKey,
		gas=None, # let web3 estimate
		value=depositEst,
		confirmPrompt=True # prompt for confirmation
	)

	# check if the subscriber was successfully subscribed
	subscribedEvMgrAddr = EthContractHelper.CallContractFunc(
		w3=w3,
		contract=subscriberContract,
		funcName='m_eventMgrAddr',
		arguments=[ ],
		privKey=None,
		gas=None,
		value=0,
		confirmPrompt=False # don't prompt for confirmation
	)
	LOGGER.info(f'Subscriber@{subscriberAddr} subscribed to EventMgr@{subscribedEvMgrAddr}')
	registeredEvMgrAddr = EthContractHelper.CallContractFunc(
		w3=w3,
		contract=publisherContract,
		funcName='m_eventMgrAddr',
		arguments=[ ],
		privKey=None,
		gas=None,
		value=0,
		confirmPrompt=False # don't prompt for confirmation
	)
	LOGGER.info(f'Publisher@{publisherAddr} registered with EventMgr@{registeredEvMgrAddr}')
	assert subscribedEvMgrAddr == registeredEvMgrAddr, 'EventMgr addresses do not match'

	LOGGER.info(f'Subscriber@{subscriberAddr} subscribed to publisher@{publisherAddr}')

	##########
	# Publish and receive
	##########

	# generate a random message to be published
	expectedMsg = random.randbytes(32).hex()

	# set message to be published
	LOGGER.info('Setting message to be published...')
	EthContractHelper.CallContractFunc(
		w3=w3,
		contract=publisherContract,
		funcName='setSendData',
		arguments=[ expectedMsg ],
		privKey=privKey,
		gas=None, # let web3 estimate
		value=0,
		confirmPrompt=False # don't prompt for confirmation
	)
	LOGGER.info('Message set to "{}"'.format(expectedMsg))

	# estimate the gas limit for publishing
	publishEstGas = (
		100000 + # est gas cost before publishing
		202000 + # gas cost for publishing
		100000   # est gas cost after publishing
	)

	# publish
	LOGGER.info('Publishing...')
	pubTxReceipt = EthContractHelper.CallContractFunc(
		w3=w3,
		contract=publisherContract,
		funcName='publish',
		arguments=[ ],
		privKey=privKey,
		gas=publishEstGas,
		value=0,
		confirmPrompt=False # don't prompt for confirmation
	)

	# ensure the subscriber received the message
	msg = EthContractHelper.CallContractFunc(
		w3=w3,
		contract=subscriberContract,
		funcName='m_recvData',
		arguments=[ ],
		privKey=None,
		gas=None,
		value=0,
		confirmPrompt=False # don't prompt for confirmation
	)
	LOGGER.info('Message received: "{}"'.format(msg))

	assert msg == expectedMsg, 'Message received does not match the expected message'


def main():
	argParser = argparse.ArgumentParser(
		description='Run tests to check compatibility with a given network'
	)
	argParser.add_argument(
		'--api-url', '-u',
		type=str, required=True,
		help='URL to the JSON-RPC over HTTP API of the network'
	)
	argParser.add_argument(
		'--key-file', '-k',
		type=str, required=True,
		help='Path to the file containing the private keys for the accounts'
	)
	argParser.add_argument(
		'--log-path', '-l',
		type=str, required=False,
		help='Path to the directory where the log file will be stored'
	)
	args = argParser.parse_args()

	logFormatter = logging.Formatter('[%(asctime)s | %(levelname)s] [%(name)s] %(message)s')
	logLevel = logging.INFO
	rootLogger = logging.root

	rootLogger.setLevel(logLevel)

	consoleHandler = logging.StreamHandler()
	consoleHandler.setFormatter(logFormatter)
	consoleHandler.setLevel(logLevel)
	rootLogger.addHandler(consoleHandler)

	if args.log_path is not None:
		fileHandler = logging.FileHandler(args.log_path)
		fileHandler.setFormatter(logFormatter)
		fileHandler.setLevel(logLevel)
		rootLogger.addHandler(fileHandler)


	RunTests(apiUrl=args.api_url, keyfile=args.key_file)


if __name__ == '__main__':
	exit(main())

