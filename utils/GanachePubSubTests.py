#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2023 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import EthContractHelper
import os
import random
import subprocess
import time

from web3 import Web3


PROJECT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'project_conf.json')
CHECKSUM_KEYS_PATH = os.path.join(os.path.dirname(__file__), 'ganache_keys_checksum.json')
GANACHE_KEYS_PATH = os.path.join(os.path.dirname(__file__), 'ganache_keys.json')
GANACHE_PORT = 7545


def StartGanache() -> subprocess.Popen:
	cmd = [
		'ganache-cli',
		'-p', str(GANACHE_PORT),
		'-d',
		'-a', '20',
		'--network-id', '1337',
		'--wallet.accountKeysPath', GANACHE_KEYS_PATH,
	]
	proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	return proc


def RunTests() -> None:
	# connect to ganache
	ganacheUrl = 'http://localhost:{}'.format(GANACHE_PORT)
	w3 = Web3(Web3.HTTPProvider(ganacheUrl))
	while not w3.is_connected():
		print('Attempting to connect to ganache...')
		time.sleep(1)
	print('Connected to ganache')

	# setup account
	privKey = EthContractHelper.SetupSendingAccount(
		w3=w3,
		account=0, # use account 0
		keyJson=CHECKSUM_KEYS_PATH
	)

	# deploy PubSub contract
	print('Deploying PubSub contract...')
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
	print('PubSub contract deployed at {}'.format(pubSubAddr))

	# load deployed PubSub contract
	pubSubContract = EthContractHelper.LoadContract(
		w3=w3,
		projConf=PROJECT_CONFIG_PATH,
		contractName='PubSubService',
		release=None, # use locally built contract
		address=pubSubAddr, # use deployed contract
	)

	# deploy Publisher contract
	print('Deploying publisher contract...')
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
	print('Publisher contract deployed at {}'.format(publisherAddr))

	# load deployed Publisher contract
	publisherContract = EthContractHelper.LoadContract(
		w3=w3,
		projConf=PROJECT_CONFIG_PATH,
		contractName='HelloWorldPublisher',
		release=None, # use locally built contract
		address=publisherAddr, # use deployed contract
	)

	# register publisher
	print('Registering publisher...')
	EthContractHelper.CallContractFunc(
		w3=w3,
		contract=publisherContract,
		funcName='register',
		arguments=[ pubSubAddr ],
		privKey=privKey,
		gas=None, # let web3 estimate
		value=0,
		confirmPrompt=False # don't prompt for confirmation
	)

	# get event manager address
	eventMgrAddr = EthContractHelper.CallContractFunc(
		w3=w3,
		contract=publisherContract,
		funcName='m_eventMgrAddr',
		arguments=[ ],
		privKey=None,
		gas=None,
		value=0,
		confirmPrompt=False # don't prompt for confirmation
	)
	print('Event manager address: {}'.format(eventMgrAddr))

	# deploy Subscriber contract
	print('Deploying subscriber contract...')
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
	print('Subscribing...')
	EthContractHelper.CallContractFunc(
		w3=w3,
		contract=subscriberContract,
		funcName='subscribe',
		arguments=[ publisherAddr ],
		privKey=privKey,
		gas=None, # let web3 estimate
		value=1000000000000000000, # 1 ether
		confirmPrompt=False # don't prompt for confirmation
	)

	# generate a random message to be published
	expectedMsg = random.randbytes(32).hex()

	# set message to be published
	print('Setting message to be published...')
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
	print('Message set to "{}"'.format(expectedMsg))

	# estimate the gas limit for publishing
	numOfSubscribers = 1
	publishEstGas = (
		90000 + # gas cost before publishing
		(numOfSubscribers * 202000) + # gas cost for publishing
		90000 # gas cost after publishing
	)

	# publish
	print('Publishing...')
	EthContractHelper.CallContractFunc(
		w3=w3,
		contract=publisherContract,
		funcName='publish',
		arguments=[ ],
		privKey=privKey,
		gas=publishEstGas,
		value=0,
		confirmPrompt=False # don't prompt for confirmation
	)

	# get the message received by the subscriber
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
	print('Message received: "{}"'.format(msg))
	if msg != expectedMsg:
		raise RuntimeError(
			'Message received does not match the expected message "{}"'.format(
				expectedMsg
			)
		)


def main():
	ganacheProc = StartGanache()

	try:
		RunTests()
	finally:
		# finish and exit
		print('Shutting down ganache (it may take ~15 seconds)...')
		ganacheProc.terminate()
		while ganacheProc.poll() is None:
			try:
				print('Still waiting for ganache to shut down...')
				ganacheProc.wait(timeout=2)
			except subprocess.TimeoutExpired:
				continue
		print('Ganache has been shut down')


if __name__ == '__main__':
	main()
