// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;


interface Interface_Subscriber {
    function onNotify(bytes memory data) external;
}


contract EventManager {

    //===== structs =====

    struct MappedSubscriber {
        bool    init;
        uint256 balanceWei;
    }

    //===== Member variables =====

    address[]                               m_subscriberAddrs;
    mapping(address => MappedSubscriber)    m_subscriberMap;
    mapping(address => bool)                m_publisherMap;

    // contract states
    address  m_owner;
    bool     m_entranceLock  = false;

    // reimbursement, gas cost, and gas limits
    uint256 m_incentiveWei   = 1000000;
    uint256 m_minDepositWei  = 100000000;
    uint256 m_perSubLimitGas = 202000;
    uint256 constant FINISHING_COST_GAS = 90000;

    //===== Events =====

    event NotifySubscribers(bytes data);

    //===== Constructor =====

    constructor(address owner) {
        // 1. set the owner of this event manager
        m_owner = owner;

        // 2. add the owner as a publisher
        m_publisherMap[owner] = true;
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
     * @dev The immediate caller must be a publisher
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
            m_publisherMap[msg.sender],
            "Only registered publisher can notify"
        );

        // 3. Get gas price (Wei per gas unit) that we want to reimburse
        uint256 gasPriceWei = tx.gasprice;

        // 4. maintain running track of how much to compensate tx.origin
        uint256 compensateWei = 0;

        uint256 numSubscribers   = m_subscriberAddrs.length;
        uint256 incentPerSubWei  = m_incentiveWei / numSubscribers;

        uint256 usedGas   = 0;
        uint256 costWei   = 0;
        uint256 limitGas  = 0;

        // 5. Make sure the specified gas limit is enough for all subscribers's
        //    max gas limit
        require(
            gasleft() >= ((m_perSubLimitGas * numSubscribers) +
                FINISHING_COST_GAS),
            "Not enough gas left"
        );
        uint fairLimitGas = (gasleft() - FINISHING_COST_GAS) / numSubscribers;

        // 6. Notify all subscribers and reimburse the sender for the gas used
        for (uint256 i = 0; i < numSubscribers; i++) {
            address subscriberAddr = m_subscriberAddrs[i];
            // get a reference to the mapped subscriber
            MappedSubscriber storage mappedSubscriber =
                m_subscriberMap[subscriberAddr];

            if (mappedSubscriber.balanceWei > incentPerSubWei) {
                // calculate how much gas unit that this subscriber can pay
                // with its balance
                limitGas =
                    (mappedSubscriber.balanceWei - incentPerSubWei) /
                        gasPriceWei;
                limitGas = limitGas > fairLimitGas ? fairLimitGas : limitGas;

                costWei = 0; // reset the cost
                usedGas = gasleft();
                try Interface_Subscriber(subscriberAddr).onNotify{
                    gas: limitGas
                }(data) {
                    // if the notification was successful, incentive will be
                    // awarded to the sender
                    costWei += incentPerSubWei;
                } catch {
                    // if the subscriber fails, we still want to reimburse
                    // the sender for the gas used, and notify the next
                    // subscriber
                }
                usedGas -= gasleft(); // (start - end)

                costWei += (usedGas * gasPriceWei);

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
     * @return uint256 The balance of the subscriber
     */
    function subscriberCheckBalance(address subscriber)
        external
        view
        returns(uint256)
    {
        // 1. check that the subscriber has been added
        require(
            m_subscriberMap[subscriber].init,
            "Subscriber is not found"
        );

        // 2. return the balance of the subscriber
        return m_subscriberMap[subscriber].balanceWei;
    }

    /**
     * This function allows the owner to update the incentive value after
     * the contract has been deployed
     * @param incentive The new incentive value
     * @dev The owner contract must call this function directly
     */
    function updateIncentive(uint256 incentive) external {
        // 1. check that the caller is the owner
        require(
            msg.sender == m_owner,
            "Only the owner can update incentive"
        );

        // 2. update the incentive
        m_incentiveWei = incentive;
    }

    /**
     * Add a publisher to share this event manager
     * @param publisherAddr The address of the publisher
     * @dev The owner contract must call this function directly
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
        m_publisherMap[publisherAddr] = true;
    }

    /**
     * Set the per subscriber minimum gas limit on the notifying call
     */
    function setPerSubscriberLimitGas(uint256 limitGas) external {
        // 1. check that the caller is the owner
        require(
            msg.sender == m_owner,
            "Only the owner can set the limit"
        );

        // 2. set the limit
        m_perSubLimitGas = limitGas;
    }

}
