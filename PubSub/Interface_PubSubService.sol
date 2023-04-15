// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;


interface Interface_PubSubService {
    function register() external returns (address);
    function subscribe(address publisherAddr, uint256 deposit) external payable;
    function getEventManagerAddr(address publisherAddr) external view returns (address);
}
