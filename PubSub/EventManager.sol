// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;


interface Interface_Subscriber {
    function onNotify(bytes memory data) external;
}


contract EventManager {

    //===== structs =====

    struct MappedSubscriber {
        bool    init;
        uint    balanceWei;
    }

    struct MappedPubPermission {
        bool    isPublisher;
    }

    //===== Member variables =====

    address[]                               m_subscriberAddrs;
    mapping(address => MappedSubscriber)    m_subscriberMap;
    mapping(address => MappedPubPermission) m_publisherMap;

    address  m_owner;
    uint     m_incentiveWei  = 1000000; // default incentive is 10000 Wei
    uint256  m_minDepositWei = 100000000;
    bool     m_entranceLock  = false;

    //===== Events =====

    event NotifySubscribers(bytes data);

    //===== Constructor =====

    constructor(address owner) {
        // 1. set the owner of this event manager
        m_owner = owner;

        // 2. add the owner as a publisher
        m_publisherMap[owner] = MappedPubPermission({
            isPublisher: true
        });
    }

    //===== external Functions =====

    /**
     * Add a subscriber to the list of subscribers
     * @param subscriberAddr The address of the subscriber
     */
    function addSubscriber(address subscriberAddr) external payable {
        // 1. check that ther subscriber has not been added
        require(
            !m_subscriberMap[subscriberAddr].init,
            "Subscriber already added"
        );

        // 2. check that the subscriber has sent enough funds
        require(
            msg.value >= m_minDepositWei,
            "You need to send at least the minimum deposit"
        );

        // 3. add the subscriber to the list of subscribers
        m_subscriberAddrs.push(subscriberAddr);

        // 4. add the subscriber to the map of subscribers
        m_subscriberMap[subscriberAddr] = MappedSubscriber({
            init:       true,
            balanceWei: msg.value
        });
    }


    /**
     * Notify all subscribers
     * @param data The data to send to the subscribers
     */
    function notifySubscribers(bytes memory data) external {
        // 1. Make sure the entrance lock is free
        require(
            !m_entranceLock,
            "Entrance lock is engaged"
        );
        m_entranceLock = true;

        // 2. Make sure the caller is a publisher
        require(
            m_publisherMap[msg.sender].isPublisher,
            "Only the registered publisher can send notifications"
        );

        // 3. Get gas price (Wei per gas unit) that we want to reimburse
        uint256 gasPriceWei = tx.gasprice;

        // 4. Notify all subscribers and reimburse the sender for the gas used

        // maintain running track of how much to compensate tx.origin
        uint256 compensateWei = 0;

        uint numSubscribers   = m_subscriberAddrs.length;
        uint incentPerSubWei  = m_incentiveWei / numSubscribers;

        uint usedGas   = 0;
        uint costWei   = 0;
        uint limitWei  = 0;
        uint limitGas  = 0;

        for (uint i = 0; i < numSubscribers; i++) {
            address subscriberAddr = m_subscriberAddrs[i];
            // get a reference to the mapped subscriber
            MappedSubscriber storage mappedSubscriber =
                m_subscriberMap[subscriberAddr];

            if (mappedSubscriber.balanceWei > incentPerSubWei) {
                limitWei = mappedSubscriber.balanceWei - incentPerSubWei;
                limitGas = limitWei / gasPriceWei;

                usedGas = gasleft();
                Interface_Subscriber(subscriberAddr).onNotify{
                    gas: limitGas
                }(data);
                usedGas -= gasleft(); // (start - end)

                costWei = (usedGas * gasPriceWei) + incentPerSubWei;

                compensateWei               += costWei;
                mappedSubscriber.balanceWei -= costWei;
            }
        }

        // reimburse the user who invoked this entire transaction
        payable(tx.origin).transfer(compensateWei);

        // 5. Release the entrance lock
        m_entranceLock = false;

        // 4. emit the event for off-chain subscribers
        emit NotifySubscribers(data);
    }

    /**
     * Make deposit to a subscriber's balance
     * @param subscriber The address of the subscriber
     */
    function subscriberAddBalance(address subscriber) external payable {
        // 1. check that the subscriber has been added
        require(
            m_subscriberMap[subscriber].init,
            "Subscriber is not found"
        );

        // 2. add the balance to the subscriber
        m_subscriberMap[subscriber].balanceWei += msg.value;
    }

    /**
     * Check the balance of a subscriber
     * @param subscriber The address of the subscriber
     * @return uint The balance of the subscriber
     */
    function subscriberCheckBalance(address subscriber) external view returns(uint) {
        // 1. check that the subscriber has been added
        require(
            m_subscriberMap[subscriber].init,
            "Subscriber is not found"
        );

        // 2. return the balance of the subscriber
        return m_subscriberMap[subscriber].balanceWei;
    }

    /**
     * Since incentive is statically set, this function enables the owner to
     * update the incentive value
     * @param incentive The new incentive value
     */
    function updateIncentive(uint incentive) external {
        // 1. check that the caller is the owner
        require(
            msg.sender == m_owner,
            "Only the owner can update the incentive"
        );

        // 2. update the incentive
        m_incentiveWei = incentive;
    }

    /**
     * Add a publisher to share this event manager
     * @param publisherAddr The address of the publisher
     */
    function addPublisher(address publisherAddr) external {
        // 1. check that the caller is the owner
        require(
            msg.sender == m_owner,
            "Only the owner can add publishers"
        );

        // Don't need to check if the publisher is already added
        // since we are just flipping a boolean

        // 2. add the publisher to the map of publishers
        m_publisherMap[publisherAddr] = MappedPubPermission({
            isPublisher: true
        });
    }


}
