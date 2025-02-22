class CertificateVerifier extends CertBlockApp {
    constructor() {
        super();
        this.setupEventListeners();
        this.html5QrcodeScanner = null;
    }

    setupEventListeners() {
        const form = document.getElementById('verifyForm');
        if (form) {
            form.addEventListener('submit', this.handleVerification.bind(this));
        }
    }

    async handleVerification(event) {
        event.preventDefault();
        const hash = document.getElementById('certificateHash').value;
        await this.verifyCertificate(hash);
    }

    async verifyCertificate(hash) {
        try {
            this.showLoading();
            await this.connectWallet();

            // Fetch certificate data from blockchain
            const result = await this.contract.methods.getCertificate(hash).call();
            
            // Fetch additional details from backend
            const response = await fetch(`/api/certificates/${hash}/`);
            const certificateData = await response.json();

            this.displayVerificationResult({
                status: result.isRevoked ? 'revoked' : 'valid',
                studentName: certificateData.student_name,
                courseName: certificateData.course_name,
                universityName: certificateData.university_name,
                issueDate: certificateData.issue_date,
                blockchainTx: certificateData.blockchain_tx
            });
        } catch (error) {
            this.displayVerificationResult({
                status: 'invalid',
                error: error.message
            });
        } finally {
            this.hideLoading();
        }
    }

    displayVerificationResult(data) {
        const resultDiv = document.getElementById('verificationResult');
        resultDiv.classList.remove('hidden');

        // Update status with appropriate styling
        const statusSpan = document.getElementById('certStatus').querySelector('span');
        statusSpan.className = 'px-2 inline-flex text-xs leading-5 font-semibold rounded-full';
        
        switch(data.status) {
            case 'valid':
                statusSpan.classList.add('bg-green-100', 'text-green-800');
                statusSpan.textContent = 'Valid';
                break;
            case 'revoked':
                statusSpan.classList.add('bg-red-100', 'text-red-800');
                statusSpan.textContent = 'Revoked';
                break;
            case 'invalid':
                statusSpan.classList.add('bg-gray-100', 'text-gray-800');
                statusSpan.textContent = 'Invalid';
                break;
        }

        // Update other certificate details
        if (data.status !== 'invalid') {
            document.getElementById('studentName').textContent = data.studentName;
            document.getElementById('courseName').textContent = data.courseName;
            document.getElementById('universityName').textContent = data.universityName;
            document.getElementById('issueDate').textContent = data.issueDate;
            document.getElementById('blockchainTx').textContent = data.blockchainTx;
        }
    }

    async startQRScanner() {
        if (!this.html5QrcodeScanner) {
            this.html5QrcodeScanner = new Html5QrcodeScanner(
                "qr-reader", { fps: 10, qrbox: 250 }
            );
        }

        this.html5QrcodeScanner.render(async (decodedText) => {
            await this.verifyCertificate(decodedText);
            this.html5QrcodeScanner.clear();
        });
    }

    showLoading() {
        document.getElementById('loadingSpinner').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loadingSpinner').classList.add('hidden');
    }
}

// Initialize the verifier
const verifier = new CertificateVerifier();

// Tab switching functionality
function switchTab(tab) {
    const tabs = ['hash', 'qr'];
    tabs.forEach(t => {
        document.getElementById(`${t}-verification`).classList.toggle('hidden', t !== tab);
        document.getElementById(`${t}-tab`).classList.toggle('active-tab', t === tab);
    });
} 