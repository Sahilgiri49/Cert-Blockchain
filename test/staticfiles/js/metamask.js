class MetaMaskIntegration extends CertBlockApp {
    constructor() {
        super();
        this.contractAddress = process.env.CONTRACT_ADDRESS || ''; // Add this to your .env file after deployment
        this.contractABI = require('../contracts/CertificateRegistry.json').abi;
        this.init();
    }

    async init() {
        if (typeof window.ethereum !== 'undefined') {
            this.web3 = new Web3(window.ethereum);
            this.contract = new this.web3.eth.Contract(this.contractABI, this.contractAddress);
            this.updateConnectionStatus();
            this.setupEventListeners();
        } else {
            this.showMetaMaskError('MetaMask is not installed');
        }
    }

    async connectWallet() {
        try {
            const accounts = await window.ethereum.request({ 
                method: 'eth_requestAccounts' 
            });
            this.account = accounts[0];
            this.updateConnectionStatus();
            return this.account;
        } catch (error) {
            if (error.code === 4001) {
                throw new Error('User rejected the connection request');
            }
            throw error;
        }
    }

    async issueCertificate(studentAddress, certificateData) {
        try {
            if (!this.account) {
                await this.connectWallet();
            }

            const certificateHash = this.web3.utils.sha3(JSON.stringify(certificateData));
            
            const gasEstimate = await this.contract.methods
                .issueCertificate(studentAddress, certificateHash)
                .estimateGas({ from: this.account });

            const result = await this.contract.methods
                .issueCertificate(studentAddress, certificateHash)
                .send({
                    from: this.account,
                    gas: Math.round(gasEstimate * 1.2) // Add 20% buffer
                });

            return {
                success: true,
                transactionHash: result.transactionHash,
                certificateHash: certificateHash
            };
        } catch (error) {
            this.handleMetaMaskError(error);
            throw error;
        }
    }

    async verifyCertificate(certificateHash) {
        try {
            if (!this.account) {
                await this.connectWallet();
            }

            const result = await this.contract.methods
                .verifyCertificate(certificateHash)
                .call();

            return {
                isValid: result.isValid,
                issuer: result.issuer,
                timestamp: result.timestamp
            };
        } catch (error) {
            this.handleMetaMaskError(error);
            throw error;
        }
    }

    async revokeCertificate(certificateHash) {
        try {
            if (!this.account) {
                await this.connectWallet();
            }

            const gasEstimate = await this.contract.methods
                .revokeCertificate(certificateHash)
                .estimateGas({ from: this.account });

            const result = await this.contract.methods
                .revokeCertificate(certificateHash)
                .send({
                    from: this.account,
                    gas: Math.round(gasEstimate * 1.2)
                });

            return {
                success: true,
                transactionHash: result.transactionHash
            };
        } catch (error) {
            this.handleMetaMaskError(error);
            throw error;
        }
    }

    handleMetaMaskError(error) {
        let message = 'An error occurred';
        
        if (error.code === 4001) {
            message = 'Transaction rejected by user';
        } else if (error.code === -32603) {
            message = 'Internal JSON-RPC error';
        } else if (error.message.includes('insufficient funds')) {
            message = 'Insufficient funds for transaction';
        }

        this.showMetaMaskError(message);
    }

    showMetaMaskError(message) {
        const event = new CustomEvent('metamaskError', { 
            detail: { message } 
        });
        window.dispatchEvent(event);
    }

    updateConnectionStatus() {
        const walletAddress = document.getElementById('walletAddress');
        if (walletAddress && this.account) {
            walletAddress.textContent = `${this.account.substring(0, 6)}...${this.account.substring(38)}`;
            walletAddress.classList.add('connected');
        }

        const connectButton = document.getElementById('connectWallet');
        if (connectButton) {
            connectButton.textContent = this.account ? 'Connected' : 'Connect Wallet';
            connectButton.classList.toggle('connected', !!this.account);
        }
    }

    setupEventListeners() {
        if (window.ethereum) {
            window.ethereum.on('accountsChanged', (accounts) => {
                this.account = accounts[0];
                this.updateConnectionStatus();
                window.location.reload();
            });

            window.ethereum.on('chainChanged', () => {
                window.location.reload();
            });

            window.ethereum.on('disconnect', () => {
                this.account = null;
                this.updateConnectionStatus();
            });
        }
    }
}

// Initialize MetaMask integration
const metaMask = new MetaMaskIntegration(); 