from web3 import Web3

class Certificate:
    def get_transaction_details(self):
        """Get transaction details from Ganache"""
        w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
        try:
            tx_hash = self.blockchain_tx
            tx_details = w3.eth.get_transaction(tx_hash)
            tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
            block = w3.eth.get_block(tx_receipt['blockNumber'])
            
            return {
                'block_number': tx_receipt['blockNumber'],
                'block_hash': tx_receipt['blockHash'].hex(),
                'transaction_hash': tx_hash,
                'from_address': tx_details['from'],
                'to_address': tx_details['to'],
                'gas_used': tx_receipt['gasUsed'],
                'timestamp': block['timestamp']
            }
        except Exception as e:
            print(f"Error getting transaction details: {e}")
            return None 