// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import {EventManager} from "./EventManager.sol"; // Import EventManager Code


contract PubSubService {
    address eventManagerAddr;
    bool eventManagerInit = false;


    event SubscribedEvent(address member);

    // constructor(address defaultEventManager, uint deposit) payable {
    constructor() {

    }


    // Deploys EventManager when Publisher wants to register with PubSub
    function register() external returns (EventManager) {
        EventManager contractAddress = new EventManager();
        eventManagerAddr = address(contractAddress); // convert contract object to address
        eventManagerInit = true;
        return contractAddress;
    }

    function subscribe(address publisher_addr, uint256 deposit, address subscribeContractAddr) external payable  {
        require(msg.value > 0, "Deposity > 0");
        require(msg.value == deposit, "Deposit what you specify");
        require(eventManagerInit == true, "Event manager not initialized");
        EventManager(eventManagerAddr).addSubscriber{value: msg.value}(publisher_addr, subscribeContractAddr); // add the subscriber to the event manager for the publisher

    }


    function getContractBalance() external view returns (uint256) {
        return address(this).balance;
    }
}
