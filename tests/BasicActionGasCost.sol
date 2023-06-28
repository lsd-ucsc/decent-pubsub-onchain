// SPDX-License-Identifier: MIT
pragma solidity >=0.4.17 <0.9.0;


contract GasEvalSubscriber {
	constructor() {
	}

	function onNotify(bytes memory data) external {
		// do nothing
	}
}


contract BasicActionGasCost {

	event LogGasCost(uint8 idx, uint256 gasUsed);

	address m_subAddr = address(0);
	bool m_someBool = false;
	mapping(address => bool) m_someMap;

	constructor() {
		GasEvalSubscriber sub = new GasEvalSubscriber();
		m_subAddr = address(sub);
	}

	function eval() external {
		bytes memory data = new bytes(0);

		uint256 gasStart = 0;
		uint256 gasUsed = 0;
		bool someBool = !m_someBool;
		address someAddr = msg.sender;

		gasStart = gasleft();
		GasEvalSubscriber(m_subAddr).onNotify(data);
		gasUsed = gasStart - gasleft();
		emit LogGasCost(1, gasUsed);

		gasStart = gasleft();
		m_someBool = someBool;
		gasUsed = gasStart - gasleft();
		emit LogGasCost(2, gasUsed);

		gasStart = gasleft();
		m_someMap[someAddr] = someBool;
		gasUsed = gasStart - gasleft();
		emit LogGasCost(3, gasUsed);
	}
}
