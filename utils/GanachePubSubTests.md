# PubSub service test with Ganache

The testing script, [`GanachePubSubTests.py`](./GanachePubSubTests.py), will
start a ganache server as a subprocess
(so you don't need to run ganache separately),
connect to ganache, and run the following tests.

## Test Coverage

1. **Deploy** `PubSubService` contract
2. **Deploy** `HelloWorldPublisher` contract
3. **Register** `HelloWorldPublisher` with `PubSubService`
4. **Deploy** `HelloWorldSubscriber` contract
5. `HelloWorldSubscriber` **subscribes** to `HelloWorldPublisher`
6. Generate a random message, and **set** the message to be sent in
   `HelloWorldPublisher`
7. `HelloWorldPublisher` **publishes** the message
8. **Get** received message from `HelloWorldSubscriber` and make sure it matches
   the message generated in step 6

## Requirement

- Python 3
- Web3.py >= 6.2.0
- Ganache
- Nodeenv

## Run the test

1. Follow the instruction in [README.md](../README.md#build-locally)
   to build the contract locally
2. Under project's root directory, run command
   `python3 utils/GanachePubSubTests.py `
