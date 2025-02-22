class CertBlockApp {
    constructor() {
        this.web3 = null;
        this.contract = null;
        this.account = null;
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        if (window.ethereum) {
            this.web3 = new Web3(window.ethereum);
        }
    }

    setupEventListeners() {
        const connectWalletBtn = document.getElementById('connectWallet');
        if (connectWalletBtn) {
            connectWalletBtn.addEventListener('click', () => this.connectWallet());
        }
    }

    async connectWallet() {
        try {
            const accounts = await window.ethereum.request({ 
                method: 'eth_requestAccounts' 
            });
            this.account = accounts[0];
            this.updateWalletUI();
        } catch (error) {
            console.error('Error connecting wallet:', error);
        }
    }

    updateWalletUI() {
        const walletBtn = document.getElementById('connectWallet');
        if (walletBtn && this.account) {
            walletBtn.textContent = `${this.account.substring(0, 6)}...${this.account.substring(38)}`;
            walletBtn.classList.remove('bg-indigo-600');
            walletBtn.classList.add('bg-green-600');
        }
    }

    async issueCertificate(studentAddress, certificateHash) {
        if (!this.web3 || !this.account) return;
        
        try {
            const result = await this.contract.methods
                .issueCertificate(certificateHash, studentAddress)
                .send({ from: this.account });
            return result;
        } catch (error) {
            console.error('Error issuing certificate:', error);
            throw error;
        }
    }

    async verifyCertificate(certificateHash) {
        if (!this.web3) return;
        
        try {
            const result = await this.contract.methods
                .verifyCertificate(certificateHash)
                .call();
            return result;
        } catch (error) {
            console.error('Error verifying certificate:', error);
            throw error;
        }
    }

    setupMetaMaskButton() {
        const metaMaskBtn = document.getElementById('connectMetaMask');
        if (metaMaskBtn) {
            metaMaskBtn.addEventListener('click', async () => {
                try {
                    await this.connectWallet();
                    metaMaskBtn.textContent = 'Connected';
                    metaMaskBtn.classList.remove('bg-indigo-100', 'text-indigo-700');
                    metaMaskBtn.classList.add('bg-green-100', 'text-green-700');
                } catch (error) {
                    console.error('MetaMask connection failed:', error);
                }
            });
        }
    }

    async showCertificateQR(certificateHash) {
        const modal = document.getElementById('qrModal');
        const qrDiv = document.getElementById('qrCode');
        
        // Generate QR code
        const qrData = `${window.location.origin}/verify/${certificateHash}`;
        const qr = new QRCode(qrDiv, {
            text: qrData,
            width: 200,
            height: 200
        });
        
        modal.classList.remove('hidden');
        
        // Close modal handler
        document.getElementById('closeQrModal').onclick = () => {
            modal.classList.add('hidden');
            qrDiv.innerHTML = ''; // Clear QR code
        };
    }

    async downloadCertificate(certificateId) {
        try {
            const response = await fetch(`/api/certificates/${certificateId}/download/`);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `certificate-${certificateId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error downloading certificate:', error);
        }
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    window.certBlockApp = new CertBlockApp();
});

// Add search functionality
document.getElementById('certificateSearch').addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase();
    const rows = document.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
}); 