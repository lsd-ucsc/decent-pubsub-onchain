// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

interface InterfacePublisher {
    function notify(address member) external;
}

contract Service {
    address[] publishers;
    mapping(address => bool) members;

    event MemberRemoved(address member);

    constructor(address member1, address member2) {
        members[member1] = true;
        members[member2] = true;
    }

    function registerPublisher(address publisher) external {
        publishers.push(publisher);
    }

    function removeMember(address member) external {
        if(members[member]) {
            delete members[member];
            emit MemberRemoved(member);

            for (uint i = 0; i < publishers.length; i++) {
                InterfacePublisher(publishers[i]).notify(member);
            }
        }
    }
}

