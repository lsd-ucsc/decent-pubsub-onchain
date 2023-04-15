// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;


interface Interface_PubSubService {
    function Register() external returns (address);
    function Subscribe(address publisherAddr, uint256 deposit) external payable;
    function GetEventManagerAddr(address publisherAddr) external view returns (address);
}
