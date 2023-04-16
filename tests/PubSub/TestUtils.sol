// SPDX-License-Identifier: MIT
pragma solidity >=0.4.17 <0.9.0;


contract DummyContract {
    constructor() {
    }
}


contract TestSubscriber{
    bytes public m_recvData;

    constructor() {
    }

    function onNotify(bytes memory data) external {
        m_recvData = data;
    }
}
