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


def _Convert(
	svg: str,
) -> str:

	return base64.b64encode(svg.encode('utf-8')).decode('utf-8')


def main():
	argParser = argparse.ArgumentParser()
	argParser.add_argument(
		'--input', type=str, required=True,
		help='input file path'
	)
	argParser.add_argument(
		'--output', type=str, required=True,
		help='output file path'
	)
	argParser.add_argument(
		'--title', type=str, required=False, default=None,
		help='title of the inlining figure'
	)
	args = argParser.parse_args()

	with open(args.input, 'r') as f:
		svg = f.read()

	converted = _Convert(svg)

	if args.title is not None:
		converted = '![{title}](data:image/svg+xml;base64,{encode} "{title}")'.format(
			title=args.title,
			encode=converted,
		)
		# converted = '<img src="data:image/svg+xml;base64,{encode}"></img>'.format(
		# 	#title=args.title,
		# 	encode=converted,
		# )

	with open(args.output, 'w') as f:
		f.write(converted)

if __name__ == '__main__':
	main()
