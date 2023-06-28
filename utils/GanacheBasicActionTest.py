#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2023 Roy Shadmon, Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import logging
import os
import signal
import subprocess
import sys
import time

from typing import List
from web3 import Web3


BASE_DIR_PATH       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR_PATH      = os.path.join(BASE_DIR_PATH, 'build')
UTILS_DIR_PATH      = os.path.join(BASE_DIR_PATH, 'utils')
PYHELPER_DIR        = os.path.join(UTILS_DIR_PATH, 'PyEthHelper')
PROJECT_CONFIG_PATH = os.path.join(UTILS_DIR_PATH, 'project_conf.json')
CHECKSUM_KEYS_PATH  = os.path.join(BUILD_DIR_PATH, 'ganache_keys_checksum.json')
GANACHE_KEYS_PATH   = os.path.join(BUILD_DIR_PATH, 'ganache_keys.json')
GANACHE_PORT        = 7545
NUM_OF_ACCOUNTS     = 100
GANACHE_NET_ID      = 1337


sys.path.append(PYHELPER_DIR)
from PyEthHelper import EthContractHelper
from PyEthHelper import GanacheAccounts


def StartGanache() -> subprocess.Popen:
	cmd = [
		'ganache-cli',
		'-p', str(GANACHE_PORT),
		'-d',
		'-a', str(NUM_OF_ACCOUNTS),
		'--network-id', str(GANACHE_NET_ID),
		'--chain.hardfork', 'shanghai',
		'--wallet.accountKeysPath', str(GANACHE_KEYS_PATH),
	]
	proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	return proc


def ReadEvalLogEvents(logs: List[dict]) -> None:
	for log in logs:
		if (
			(len(log['topics']) > 0) and
			(
				log['topics'][0].hex() ==
				'0xe1ae46340cc3bb84afacee6678b86b538a6d5e4ce754adb3bfa9ce4e41d196ba'
			)
		):
			hexData = log['data'].hex()
			assert len(hexData) == 2 + (2 * (32 + 32)), 'Invalid log data length'
			bData = bytes.fromhex(hexData[2:])
			idx = int.from_bytes(bData[:32], byteorder='big')
			gasUsed = int.from_bytes(bData[32:], byteorder='big')
			print(f'Evaluated action at index {idx} with gas used {gasUsed}')


def RunTests() -> dict:
	# connect to ganache
	ganacheUrl = 'http://localhost:{}'.format(GANACHE_PORT)
	w3 = Web3(Web3.HTTPProvider(ganacheUrl))
	while not w3.is_connected():
		print('Attempting to connect to ganache...')
		time.sleep(1)
	print('Connected to ganache')

	# checksum keys
	GanacheAccounts.ChecksumGanacheKeysFile(
		CHECKSUM_KEYS_PATH,
		GANACHE_KEYS_PATH
	)

	# setup account
	privKey = EthContractHelper.SetupSendingAccount(
		w3=w3,
		account=0,
		keyJson=CHECKSUM_KEYS_PATH
	)

	# deploy BasicActionGasCost contract
	print('Deploying BasicActionGasCost contract...')
	baContract = EthContractHelper.LoadContract(
		w3=w3,
		projConf=PROJECT_CONFIG_PATH,
		contractName='BasicActionGasCost',
		release=None, # use locally built contract
		address=None, # deploy new contract
	)
	baReceipt = EthContractHelper.DeployContract(
		w3=w3,
		contract=baContract,
		arguments=[ ],
		privKey=privKey,
		gas=None, # let web3 estimate
		value=0,
		confirmPrompt=False # don't prompt for confirmation
	)
	baAddr = baReceipt.contractAddress
	print('BasicActionGasCost contract deployed at {}'.format(baAddr))

	# load deployed BasicActionGasCost contract
	baContract = EthContractHelper.LoadContract(
		w3=w3,
		projConf=PROJECT_CONFIG_PATH,
		contractName='BasicActionGasCost',
		release=None, # use locally built contract
		address=baAddr, # use deployed contract
	)

	evalTxReceipt = EthContractHelper.CallContractFunc(
		w3=w3,
		contract=baContract,
		funcName='eval',
		arguments=[ ],
		privKey=privKey,
		gas=None, # let web3 estimate
		value=0,
		confirmPrompt=False # don't prompt for confirmation
	)
	ReadEvalLogEvents(evalTxReceipt.logs)


def StopGanache(ganacheProc: subprocess.Popen) -> None:
	print('Shutting down ganache (it may take ~15 seconds)...')
	waitEnd = time.time() + 20
	ganacheProc.terminate()
	while ganacheProc.poll() is None:
		try:
			if time.time() > waitEnd:
				print('Force to shut down ganache')
				ganacheProc.kill()
			else:
				print('Still waiting for ganache to shut down...')
				ganacheProc.send_signal(signal.SIGINT)
			ganacheProc.wait(timeout=2)
		except subprocess.TimeoutExpired:
			continue
	print('Ganache has been shut down')


def main():
	logging.basicConfig(
		level=logging.DEBUG,
		format='%(asctime)s %(levelname)s %(name)s %(message)s'
	)

	ganacheProc = StartGanache()

	try:
		RunTests()

	finally:
		# finish and exit
		StopGanache(ganacheProc)


if __name__ == "__main__":
	main()

