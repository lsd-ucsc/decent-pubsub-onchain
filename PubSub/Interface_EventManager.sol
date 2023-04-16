// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;


interface Interface_EventManager {

    /**
     * Add a subscriber to the list of subscribers
     * @param subscriberAddr The address of the subscriber
     */
    function addSubscriber(address subscriberAddr) external payable;

    /**
     * Notify all subscribers
     * @param data The data to send to the subscribers
     */
    function notifySubscribers(bytes memory data) external;

    /**
     * Make deposit to a subscriber's balance
     * @param subscriber The address of the subscriber
     */
    function subscriberAddBalance(address subscriber) external payable;

    /**
     * Check the balance of a subscriber
     * @param subscriber The address of the subscriber
     * @return uint The balance of the subscriber
     */
    function subscriberCheckBalance(address subscriber)
        external
        view
        returns(uint);

    /**
     * This function allows the owner to update the incentive value after
     * the contract has been deployed
     * @param incentive The new incentive value
     */
    function updateIncentive(uint incentive) external;

    /**
     * Add a publisher to share this event manager
     * @param publisherAddr The address of the publisher
     */
    function addPublisher(address publisherAddr) external;
}
