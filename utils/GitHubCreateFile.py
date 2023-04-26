#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2023 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import argparse
import base64
import os
import requests

from typing import List


def BuildTreeObj(
	path: str,
	sha: str,
	mode: str = '100644',
	type: str = 'blob',
) -> dict:
	return {
		'path': path,
		'mode': mode,
		'type': type,
		'sha': sha,
	}


def GitBlobCreateText(
	owner: str,
	repo: str,
	token: str,
	content: str,
) -> dict:
	# https://docs.github.com/en/rest/git/blobs?apiVersion=2022-11-28#create-a-blob

	url = f'https://api.github.com/repos/{owner}/{repo}/git/blobs'
	req = requests.post(
		url=url,
		headers={
			'Accept': 'application/vnd.github+json',
			'Authorization': f'Bearer {token}',
		},
		json={
			'content': content,
			'encoding': 'utf-8',
		},
	)
	req.raise_for_status()

	return req.json()


def GitTreeCreate(
	owner: str,
	repo: str,
	token: str,
	baseTree: str,
	trees: List[dict],
) -> dict:
	# https://docs.github.com/en/rest/git/trees?apiVersion=2022-11-28

	url = f'https://api.github.com/repos/{owner}/{repo}/git/trees'
	req = requests.post(
		url=url,
		headers={
			'Accept': 'application/vnd.github+json',
			'Authorization': f'Bearer {token}',
		},
		json={
			'base_tree': baseTree,
			'tree': trees,
		},
	)
	req.raise_for_status()

	return req.json()


def ContentsCreateFile(
	owner: str,
	repo: str,
	token: str,
	path: str,
	commitMsg: str,
	contentB64: str,
	branch: str,
) -> dict:
	#https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28#create-or-update-file-contents

	url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
	req = requests.put(
		url=url,
		headers={
			'Accept': 'application/vnd.github+json',
			'Authorization': f'Bearer {token}',
		},
		json={
			'message': commitMsg,
			'content': contentB64,
			'branch': branch,
		},
	)
	req.raise_for_status()

	return req.json()


def main() -> None:
	argParser = argparse.ArgumentParser()
	argParser.add_argument(
		'--path', type=str, required=True,
		help='File path in repo',
	)
	argParser.add_argument(
		'--commit-msg', type=str, required=True,
		help='Commit message',
	)
	argParser.add_argument(
		'--file', type=str, required=True,
		help='File path to upload',
	)
	argParser.add_argument(
		'--branch', type=str, required=True,
		help='Branch name',
	)
	args = argParser.parse_args()

	# get owner and repo from environment variable
	ownerAndRepo = os.environ.get('GITHUB_REPOSITORY')
	if ownerAndRepo is None:
		raise ValueError('GITHUB_REPOSITORY is not set')
	owner, repo = ownerAndRepo.split('/', maxsplit=1)

	# get token from environment variable
	token = os.environ.get('GITHUB_TOKEN')
	if token is None:
		raise ValueError('GITHUB_TOKEN is not set')

	# read in file
	with open(args.file, 'rb') as f:
		content = f.read()

	# convert to base64
	contentB64 = base64.b64encode(content).decode('utf-8')

	ContentsCreateFile(
		owner=owner,
		repo=repo,
		token=token,
		path=args.path,
		commitMsg=args.commit_msg,
		contentB64=contentB64,
		branch=args.branch,
	)


if __name__ == '__main__':
	main()
