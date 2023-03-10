// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import {EventManager} from "./EventManager.sol"; // Import EventManager Code


// interface InterfaceEventManager {
//     function subscribe(address user, uint balance) external payable;
//     function notify(address member) external;
// }

contract PubSubService {
    address eventManagerAddr;
    bool eventManagerInit = false;


    event SubscribedEvent(address member);

    // constructor(address defaultEventManager, uint deposit) payable {
    constructor(uint deposit) payable {
        require(deposit == msg.value, "Deposit what you send");
    }

    // function publish(address member) external {
    //     emit SubscribedEvent(member);
    // }


    // Deploys EventManager when Publisher wants to register with PubSub
    function register(uint deposit) payable external returns (EventManager) {
        require(msg.value > 0, "Deposity > 0");
        require(deposit == msg.value, "Deposit what you send");
        EventManager contractAddress = new EventManager{value: msg.value}(msg.value);
        eventManagerAddr = address(contractAddress); // convert contract object to address
        eventManagerInit = true;
        return contractAddress;
    }

    function subscribe(address publisher_addr, uint deposit, address subscribeContractAddr) external payable {
        require(msg.value > 0, "Deposity > 0");
        require(msg.value == deposit, "Deposit what you specify");
        require(eventManagerInit == true, "Event manager not initialized");
        EventManager(eventManagerAddr).addSubscriber{value: msg.value}(publisher_addr, payable(msg.sender), subscribeContractAddr); // add the subscriber to the event manager for the publisher

    }


    function getContractBalance() public view returns (uint256) {
        return address(this).balance;
    }
}
