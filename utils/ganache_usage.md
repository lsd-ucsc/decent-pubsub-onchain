# Ganache

## To start Ganache, create new keys, and add keys to keys directory:
```
ganache-cli -a 20 --network-id 1337 --wallet.accountKeysPath [path_to_decent_lib]/decent-pubsub-onchain/utils/ganache_keys.json
```

## Start Ganache with existing keys.json folder existing:
```
ganache-cli -d -a 20 --network-id 1337
```

## Notes
```
-d = deterministic (deterministic private keys for testing)
-a 20 = create 20 accounts
```
