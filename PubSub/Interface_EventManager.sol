// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;


interface Interface_EventManager {
    function AddSubscriber(address subscriberAddr) external payable;
    function Notify(bytes memory data) external;
    function SubscriberAddBalance(address subscriber) external payable;
    function SubscriberCheckBalance(address subscriber) external view returns(uint);
    function UpdateIncentive(uint incentive) external;
    function AddPublisher(address publisherAddr) external;
}
