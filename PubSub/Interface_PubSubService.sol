// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;


interface Interface_PubSubService {

    /**
     * Register a publisher with the PubSubService and spawn a new
     * corresponding EventManager contract
     * @return address The address of the newly created EventManager contract
     * @dev The publisher contract must call this function to register
     */
    function register() external returns (address);

    /**
     * Subscribe a subscriber to a publisher's event manager
     * @param publisherAddr The address of the publisher
     * @dev The subscriber contract must call this function to subscribe
     */
    function subscribe(address publisherAddr) external payable;

    /**
     * Get the EventManager contract address for a publisher
     * @param publisherAddr The address of the publisher
     * @return address The address of the EventManager contract
     */
    function getEventManagerAddr(address publisherAddr)
        external
        view
        returns (address);
}
