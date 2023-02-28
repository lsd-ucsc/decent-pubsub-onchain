// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

interface InterfaceEventManager {
    function subscribe(address user, uint balance) external payable;
    function notify(address member) external;
}

contract PubSubService {
    address eventManager;

    event SubscribedEvent(address member);

    constructor(address defaultEventManager, uint deposit) payable {
        require(deposit == msg.value, "Deposit what you send");
        eventManager = defaultEventManager;
        InterfaceEventManager(defaultEventManager).subscribe{value: msg.value}(payable(msg.sender), msg.value);
    }

    function publish(address member) external {
        emit SubscribedEvent(member);
    }


    function getContractBalance() public view returns (uint256) {
        return address(this).balance;
    }
}
