// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

interface InterfacePublisher {
    function subscribe(address user, uint balance) external payable;
    function notify(address member) external;
}

contract Subscriber {
    address publisher;

    event SubscribedEvent(address member);

    constructor(address defaultPublisher, uint deposit) payable {
        require(deposit == msg.value, "Deposit what you send");
        publisher = defaultPublisher;
        InterfacePublisher(publisher).subscribe{value: msg.value}(payable(msg.sender), msg.value);
    }

    function publish(address member) external {
        emit SubscribedEvent(member);
    }


    function getContractBalance() public view returns (uint256) {
        return address(this).balance;
    }
}
