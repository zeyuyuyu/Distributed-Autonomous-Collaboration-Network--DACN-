import random
import hashlib
import time

class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        sha = hashlib.sha256()
        sha.update(str(self.index).encode('utf-8'))
        sha.update(str(self.timestamp).encode('utf-8'))
        sha.update(str(self.data).encode('utf-8'))
        sha.update(str(self.previous_hash).encode('utf-8'))
        return sha.hexdigest()

class BlockchainNode:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.pending_transactions = []
        self.mining_reward = 50

    def create_genesis_block(self):
        return Block(0, time.time(), "Genesis Block", "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_transaction(self, transaction):
        self.pending_transactions.append(transaction)

    def mine_block(self, miner_address):
        block = Block(len(self.chain), time.time(), self.pending_transactions, self.get_latest_block().hash)
        self.chain.append(block)
        self.pending_transactions = []
        self.add_transaction({"from": "system", "to": miner_address, "amount": self.mining_reward})
        return block

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            if current_block.hash != current_block.calculate_hash():
                return False
            if current_block.previous_hash != previous_block.hash:
                return False
        return True

class DecentralizedConsensus:
    def __init__(self, nodes):
        self.nodes = nodes
        self.difficulty_target = 4

    def consensus(self):
        longest_chain = None
        max_length = len(self.nodes[0].chain)

        for node in self.nodes:
            if len(node.chain) > max_length and node.is_chain_valid():
                max_length = len(node.chain)
                longest_chain = node.chain

        if longest_chain:
            for node in self.nodes:
                node.chain = longest_chain
        else:
            print("No consensus reached.")

    def proof_of_work(self, block):
        block.nonce = 0
        computed_hash = block.calculate_hash()
        while not computed_hash.startswith('0' * self.difficulty_target):
            block.nonce += 1
            computed_hash = block.calculate_hash()
        return computed_hash

    def mine_and_broadcast(self, node):
        block = node.mine_block(node.address)
        computed_hash = self.proof_of_work(block)
        block.hash = computed_hash
        self.consensus()
        for n in self.nodes:
            if n != node:
                n.chain.append(block)
        return block

if __name__ == '__main__':
    node1 = BlockchainNode()
    node1.address = "Node1"
    node2 = BlockchainNode()
    node2.address = "Node2"
    node3 = BlockchainNode()
    node3.address = "Node3"

    nodes = [node1, node2, node3]
    consensus = DecentralizedConsensus(nodes)

    node1.add_transaction({"from": "Alice", "to": "Bob", "amount": 10})
    node2.add_transaction({"from": "Bob", "to": "Charlie", "amount": 5})
    node3.add_transaction({"from": "Charlie", "to": "Alice", "amount": 3})

    consensus.mine_and_broadcast(node1)
    consensus.mine_and_broadcast(node2)
    consensus.mine_and_broadcast(node3)

    print("Blockchain valid?", node1.is_chain_valid())
