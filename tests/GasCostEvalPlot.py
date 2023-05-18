#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Copyright (c) 2023 Haofan Zheng
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
###


import json
import os
import time
from typing import List, Tuple, Union

import plotly.graph_objects as go
import plotly.express as px


BASE_DIR_PATH       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR_PATH      = os.path.join(BASE_DIR_PATH, 'build')


ErrorBarData = List[int]
SingleData   = int
DataPoint    = Tuple[int, Union[SingleData, ErrorBarData]]
DataPoints   = List[DataPoint]


# available markers: https://plotly.com/python/marker-style/
# circle, square, diamond, cross, x, triangle, pentagon, hexagram, star, diamond, hourglass, bowtie, asterisk, hash, y
# available colors: https://plotly.com/python/discrete-color/
POINT_MARKERS = [
	{
		'size': 8,
		'symbol': 'circle',
		'color': px.colors.qualitative.Plotly[0],
	},
	{
		'size': 8,
		'symbol': 'square',
		'color': px.colors.qualitative.Plotly[1],
	},
	{
		'size': 8,
		'symbol': 'diamond',
		'color': px.colors.qualitative.Plotly[2],
	},
]


def GenerateFigure(
	inData: List[DataPoints],
	dataNames: List[str],
	xLabel: str,
	yLabel: str,
	title: str,
	marks: List[dict] = POINT_MARKERS,
) -> go.Figure:

	topSpace = 50 if title else 10
	layout = go.Layout(
		autosize=True,
		margin={ 'l': 10, 'r': 10, 't': topSpace, 'b': 10, }
	)
	fig    = go.Figure(layout=layout)
	fig.update_layout(
		legend=dict(
			yanchor="top",
			y=0.99,
			xanchor="left",
			x=0.01
		),
		title=title,
		xaxis_title=xLabel,
		yaxis_title=yLabel,
	)

	for ds, dName, mark in zip(inData, dataNames, marks):
		hasErrBar = type(ds[0][1]) == list
		if hasErrBar:
			yNormal = [ y[1] for _, y in ds ]
			yPlus   = [ y[2] - y[1] for _, y in ds ]
			yMinus  = [ y[1] - y[0] for _, y in ds ]
			fig.add_trace(
				go.Scatter(
					x=[ x    for x, _ in ds ],
					y=yNormal,
					error_y=dict(
						type='data',
						array=yPlus,
						arrayminus=yMinus,
					),
					name=dName,
					mode='lines+markers',
					marker=mark,
				)
			)
		else:
			fig.add_trace(
				go.Scatter(
					x=[ x for x, _ in ds ],
					y=[ y for _, y in ds ],
					name=dName,
					mode='lines+markers',
					marker=mark,
				)
			)

	fig.update_xaxes(tickmode='linear')
	fig.update_yaxes(tickformat="none")

	return fig


def SaveFigure(
	fig: go.Figure,
	outName: str,
) -> None:
	fig.write_image(outName + '.svg')

	fig.write_image(outName + '.pdf')
	# mitigation for issue https://github.com/plotly/plotly.py/issues/3469
	time.sleep(2)
	fig.write_image(outName + '.pdf')


def PlotGraph(
	inData: List[DataPoints],
	dataNames: List[str],
	xLabel: str,
	yLabel: str,
	title: str,
	outName: str,
	marks: List[dict] = POINT_MARKERS,
) -> None:
	fig = GenerateFigure(inData, dataNames, xLabel, yLabel, title, marks)

	SaveFigure(fig, outName)


def ReadResults(
	inputPath: os.PathLike,
) -> DataPoints:
	with open(inputPath, 'r') as f:
		results = json.load(f)

	# convert list of 3 test results to results with min & max
	assert len(results) == 3, 'Expected 3 test results'
	assert len(results[0]) == len(results[1]) == len(results[2]), \
		'Expected 3 test results with same length'

	processedResults = []
	for testRes1, testRes2, testRes3 in zip(*results):
		assert testRes1[0] == testRes2[0] == testRes3[0], \
			'Expected 3 test results with same X axis value'

		processedResults.append((
			testRes1[0], # x axis value
			sorted(
				[
					testRes1[1],
					testRes2[1],
					testRes3[1],
				]
			) # y axis value, in ascending order
		))

	# check if it is necessary to keep min & max
	for _, ys in processedResults:
		if not(ys[0] == ys[1] == ys[2]):
			# need to keep min & max
			return processedResults

	# all 3 results are the same
	# no need to keep min & max
	return [
		(x, y[1])
		for x, y in processedResults
	]


def main() -> None:
	pubGasCostRes = ReadResults(
		os.path.join(BUILD_DIR_PATH, 'publish_gas_cost.json')
	)

	PlotGraph(
		inData=[ pubGasCostRes ],
		dataNames=[ 'Publish Costs' ],
		title='Publish Gas Cost',
		xLabel='Number of Subscribers',
		yLabel='Amount of Gas Units',
		outName=os.path.join(BUILD_DIR_PATH, 'publish_gas_cost'),
	)

	subGasCostRes = ReadResults(
		os.path.join(BUILD_DIR_PATH, 'subscribe_gas_cost.json')
	)

	fig2 = GenerateFigure(
		inData=[ subGasCostRes ],
		dataNames=[ 'Subscribe Costs' ],
		title='Subscribe Gas Cost',
		xLabel='Number of Publishers',
		yLabel='Amount of Gas Units',
	)
	fig2YMax = max([ y[2] for _, y in subGasCostRes ])
	fig2YMin = min([ y[0] for _, y in subGasCostRes ])
	fig2YMid = (fig2YMax + fig2YMin) / 2
	fig2YMax += fig2YMid * 0.00005
	fig2YMin -= fig2YMid * 0.00005
	fig2.update_yaxes(range=[fig2YMin, fig2YMax])
	SaveFigure(
		fig=fig2,
		outName=os.path.join(BUILD_DIR_PATH, 'subscribe_gas_cost'),
	)

	PlotGraph(
		inData=[ pubGasCostRes, subGasCostRes, ],
		dataNames=[ 'Publish Costs', 'Subscribe Costs', ],
		title='Publish & Subscribe Gas Cost',
		xLabel='Number of Subscribers/Publishers',
		yLabel='Amount of Gas Units',
		outName=os.path.join(BUILD_DIR_PATH, 'gas_cost'),
	)


if __name__ == '__main__':
	main()
