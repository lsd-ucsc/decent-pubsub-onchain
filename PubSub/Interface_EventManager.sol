// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;


interface Interface_EventManager {
    function addSubscriber(address subscriberAddr) external payable;
    function notifySubscribers(bytes memory data) external;
    function subscriberAddBalance(address subscriber) external payable;
    function subscriberCheckBalance(address subscriber) external view returns(uint);
    function updateIncentive(uint incentive) external;
    function addPublisher(address publisherAddr) external;
}
