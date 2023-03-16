package main

import (
	"bytes"
	"context"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"math/big"
	"net/http"
	"time"

	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/core/types"
	"github.com/ethereum/go-ethereum/crypto"
	"github.com/ethereum/go-ethereum/ethclient"
	"github.com/ethereum/go-ethereum/rlp"
)

const (
	STARTBLOCK     = 8627000
	ENDBLOCK       = 8629000
	LOCAL_ENDPOINT = "http://127.0.0.1:8545/"
)

var (
	BlockNums []string
	RlpResp   map[string]interface{}

	EthBlock  *types.Block
	EthHeader *types.Header

	HeaderRlpResp string
)

type PayloadBlock struct {
	Method  string `json:"method"`
	Params  []any  `json:"params"`
	ID      int    `json:"id"`
	Jsonrpc string `json:"jsonrpc"`
}

func PanicIfError(err error) {
	if err != nil {
		panic(err)
	}
}

func GenerateBlockNums() {
	for i := STARTBLOCK; i < ENDBLOCK; i++ {
		BlockNums = append(BlockNums, fmt.Sprintf("0x%x", i))
	}
}

// bloomValues is a private function in geth I've copied it and added in some print statements to show you how it works
// See here for function in geth codebase https://github.com/ethereum/go-ethereum/blob/d8ff53dfb8a516f47db37dbc7fd7ad18a1e8a125/core/types/bloom9.go#L139
func bloomValues(data []byte, hashbuf []byte) (uint, byte, uint, byte, uint, byte) {
	var hashed = crypto.Keccak256(data)
	hashbuf = hashed[:6]

	// The actual bits to flip
	v1 := byte(1 << (hashbuf[1] & 0x7))
	v2 := byte(1 << (hashbuf[3] & 0x7))
	v3 := byte(1 << (hashbuf[5] & 0x7))

	// The indices for the bytes to OR in
	i1 := types.BloomByteLength - uint((binary.BigEndian.Uint16(hashbuf)&0x7ff)>>3) - 1
	i2 := types.BloomByteLength - uint((binary.BigEndian.Uint16(hashbuf[2:])&0x7ff)>>3) - 1
	i3 := types.BloomByteLength - uint((binary.BigEndian.Uint16(hashbuf[4:])&0x7ff)>>3) - 1

	return i1, v1, i2, v2, i3, v3
}

func CheckBloomBits(bloom []byte, data ...[]byte) bool {
	buf := make([]byte, 6)
	var i1, i2, i3 uint
	var v1, v2, v3 byte

	for _, d := range data {
		i1, v1, i2, v2, i3, v3 = bloomValues(d, buf)
		inBloom := (bloom[i1]&v1 != 0 && bloom[i2]&v2 != 0 && bloom[i3]&v3 != 0)
		if !inBloom {
			return false
		}
	}
	return true
}

func StringToBytes(str string) []byte {
	str = str[2:]
	strBytes := common.FromHex(str)

	return strBytes
}

func ExecuteRequest(requestBody *bytes.Reader) map[string]interface{} {
	req, _ := http.NewRequest("POST", LOCAL_ENDPOINT, requestBody)
	req.Header.Set("Content-Type", "application/json")
	resp, _ := http.DefaultClient.Do(req)

	defer resp.Body.Close()

	// decode response into a map to extract result
	err := json.NewDecoder(resp.Body).Decode(&RlpResp)
	PanicIfError(err)

	return RlpResp
}

func GetPayload(method string, blockNumHash string) *bytes.Reader {
	data := PayloadBlock{
		Method:  method,
		Params:  []any{blockNumHash},
		ID:      1,
		Jsonrpc: "2.0",
	}
	payloadBytes, _ := json.Marshal(data)
	payload := bytes.NewReader(payloadBytes)
	return payload
}

func HexStrToBytes(hexStr string) []byte {
	hexStr = hexStr[2:]
	resBytes := common.FromHex(hexStr)

	return resBytes
}

/*
Iterate over a sequence of block numbers and retrieve the RLP-encoded header for each block.
*/
func HeaderThroughput() {
	numBlocks := len(BlockNums)
	startTime := time.Now()

	for i := 0; i < numBlocks; i++ {
		payload := GetPayload("debug_getRawHeader", BlockNums[i])
		headerRlp := ExecuteRequest(payload)
		headerBytes := StringToBytes(headerRlp["result"].(string))

		if len(headerBytes) == 0 {
			fmt.Println("header bytes is empty")
		}
	}

	endTime := time.Now()
	throughput := float64(numBlocks) / float64(endTime.Sub(startTime).Milliseconds()) * 1000
	fmt.Println("header throughput: ", throughput)
}

/*
Iterate over a sequence of block numbers and retrieve the RLP-encoded blocks
*/
func BlockThroughput() {
	numBlocks := len(BlockNums)
	startTime := time.Now()

	for i := 0; i < numBlocks; i++ {
		payload := GetPayload("debug_getRawBlock", BlockNums[i])
		blockRlp := ExecuteRequest(payload)
		blockBytes := StringToBytes(blockRlp["result"].(string))

		EthBlock = new(types.Block)
		if err := rlp.Decode(bytes.NewReader(blockBytes), &EthBlock); err != nil {
			PanicIfError(err)
		}

		// check if block hash matches
		if EthBlock.Hash() != EthBlock.Header().Hash() {
			fmt.Errorf("block hash does not match header hash")
		}
	}

	endTime := time.Now()
	throughput := float64(numBlocks) / float64(endTime.Sub(startTime).Milliseconds()) * 1000
	fmt.Println("block throughput: ", throughput)
}

func HeaderBloomThroughput() {
	eventSigHash := crypto.Keccak256([]byte("SyncMsg(bytes16,bytes32)"))
	sessionId := common.Hex2Bytes("52fdfc072182654f163f5f0f9a621d7200000000000000000000000000000000")
	nonce := common.Hex2Bytes("9566c74d10037c4d7bbb0407d1e2c64981855ad8681d0d86d1e91e00167939cb")

	numBlocks := len(BlockNums)
	startTime := time.Now()

	for i := 0; i < numBlocks; i++ {
		payload := GetPayload("debug_getRawHeader", BlockNums[i])
		headerRlp := ExecuteRequest(payload)
		headerBytes := StringToBytes(headerRlp["result"].(string))

		EthHeader = new(types.Header)
		if err := rlp.Decode(bytes.NewReader(headerBytes), &EthHeader); err != nil {
			PanicIfError(err)
		}

		// check if event signature, sessionId, and nonce are in the header bloom
		headerBloom := EthHeader.Bloom.Bytes()
		if CheckBloomBits(headerBloom, eventSigHash, sessionId, nonce) {
			fmt.Println("event found in header bloom")
		}
	}

	endTime := time.Now()
	throughput := float64(numBlocks) / float64(endTime.Sub(startTime).Milliseconds()) * 1000
	fmt.Println("header bloom throughput: ", throughput)
}

func CheckReceipt(receipt *types.Receipt, eventDetails [3][]byte) bool {
	if len(receipt.Logs) > 0 {
		topics := receipt.Logs[0].Topics
		if len(topics) == len(eventDetails) {
			match := true
			for j := 0; j < len(eventDetails); j++ {
				if !bytes.Equal(eventDetails[j], topics[j].Bytes()) {
					return false
				}
			}
			if match {
				fmt.Println("event sig: ", topics[0].Hex())
				return true
			}
		}
	}
	return false
}

func EventInReceipts(receiptsRlp []interface{}, eventDetails [3][]byte) bool {
	eventFound := false
	numReceipts := len(receiptsRlp)
	for i := 0; i < numReceipts; i++ {
		receipt := new(types.Receipt)
		receiptStr := receiptsRlp[i].(string)
		receiptsBytes := HexStrToBytes(receiptStr)

		if err := receipt.UnmarshalBinary(receiptsBytes); err != nil {
			PanicIfError(err)
		}

		if CheckReceipt(receipt, eventDetails) {
			eventFound = true
			break
		}
	}
	return eventFound
}

func BloomAndReceiptThroughput() {
	eventSigHash := crypto.Keccak256([]byte("SyncMsg(bytes16,bytes32)"))
	sessionId := common.Hex2Bytes("52fdfc072182654f163f5f0f9a621d7200000000000000000000000000000000")
	nonce := common.Hex2Bytes("9566c74d10037c4d7bbb0407d1e2c64981855ad8681d0d86d1e91e00167939cb")
	eventDetails := [3][]byte{eventSigHash, sessionId, nonce}

	numBlocks := len(BlockNums)
	startTime := time.Now()

	for i := 0; i < numBlocks; i++ {
		requestPayload := GetPayload("debug_getRawHeader", BlockNums[i])
		headerRlp := ExecuteRequest(requestPayload)
		headerBytes := StringToBytes(headerRlp["result"].(string))

		if err := rlp.Decode(bytes.NewReader(headerBytes), &EthHeader); err != nil {
			PanicIfError(err)
		}
		// check if event signature, sessionId, and nonce are in the header bloom
		headerBloom := EthHeader.Bloom.Bytes()
		if CheckBloomBits(headerBloom, eventSigHash, sessionId, nonce) {
			requestPayload := GetPayload("debug_getRawReceipts", BlockNums[i])
			resultsRlp := ExecuteRequest(requestPayload)
			receiptsRlp := resultsRlp["result"].([]interface{})

			eventFound := EventInReceipts(receiptsRlp, eventDetails)
			if eventFound {
				fmt.Println("found event in receipt bloom")
			} else {
				fmt.Println("false positive")
			}
		}
	}

	endTime := time.Now()
	throughput := float64(numBlocks) / float64(endTime.Sub(startTime).Milliseconds()) * 1000
	fmt.Println("bloom and receipt throughput: ", throughput)
}

func main() {
	GenerateBlockNums()

	//// Throughput tests
	HeaderThroughput()
	BlockThroughput()
	HeaderBloomThroughput()
	BloomAndReceiptThroughput()

	//// Test functions
	// ethClient := GetEthClient(LOCAL_ENDPOINT)
	// CheckBlockForEvent(big.NewInt(8628615), ethClient)
}

/**
******************************************************
					Test Functions
******************************************************
*/

func GetEthClient(endpoint string) *ethclient.Client {
	client, err := ethclient.Dial(endpoint)
	PanicIfError(err)

	return client
}

func CheckBlockForEvent(blocknum *big.Int, client *ethclient.Client) {
	eventSig := []byte("SyncMsg(bytes16,bytes32)")
	hash := crypto.Keccak256(eventSig)
	eventSigHash := common.BytesToHash(hash)
	fmt.Println("eventSigHash: ", hash)

	block, err := client.BlockByNumber(context.Background(), blocknum)
	PanicIfError(err)

	contractAddr := "0x74Be867FBD89bC3507F145b36ba76cd0B1bF4f1A"
	SyncContractAddr := common.HexToAddress(contractAddr)

	txns := block.Transactions()
	numTxns := len(txns)
	var txnHash common.Hash
	found := false
	for i := 0; i < numTxns; i++ {
		to := txns[i].To()
		if to != nil && *to == SyncContractAddr {
			txnHash = txns[i].Hash()
			found = true
			fmt.Println("sync contract address found")
		}
	}

	if found {
		receipt, err := client.TransactionReceipt(context.Background(), txnHash)
		PanicIfError(err)

		logs := receipt.Logs
		topics := logs[0].Topics

		if topics[0] == eventSigHash {
			fmt.Println("sync event found")
			fmt.Println("event parameters: ")

			for i := 1; i < len(topics); i++ {
				fmt.Println(topics[i].Bytes())
			}
		}
	}
}
