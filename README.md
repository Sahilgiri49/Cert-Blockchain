# CertChain - Blockchain Certificate Verification System

## Overview

CertChain is a decentralized application (dApp) designed to provide a secure, tamper-proof, and decentralized method for issuing, storing, and verifying academic certificates using blockchain technology. 

## Features

- **Decentralized Certificate Storage**: Uses blockchain to store and verify certificates securely.
- **Smart Contract-Based Issuance**: Universities issue certificates via smart contracts.
- **IPFS Integration**: Stores certificate metadata on IPFS for decentralized access.
- **Role-Based Access Control**: Universities, students, and employers have distinct access permissions.
- **QR Code Verification**: Users can scan QR codes to verify certificates easily.
- **MetaMask Integration**: Allows secure interactions with Ethereum smart contracts.

## Tech Stack

### Blockchain
- Ethereum (Solidity for smart contracts)
- OpenZeppelin (for security and role management)
- IPFS (for storing metadata and certificate files)

### Backend
- Django (Handles authentication and database management)
- MongoDB (Stores certificate request and verification data)
- Web3.py (Interacts with smart contracts)

### Frontend
- React.js (for UI)
- Tailwind CSS (for styling)
- Web3.js (for blockchain interactions)

---

## Installation and Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/CertChain.git
cd CertChain
```

### 2. Install Dependencies
#### Backend (Django)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 3. Start the Server
```bash
cd test
python manage.py runserver
```

### 4. Start the Ganache application

## Smart Contracts

### CertificateContract.sol
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract CertificateContract {
    struct Certificate {
        bytes32 certificateHash;
        address issuer;
        address student;
        bool isRevoked;
        uint256 timestamp;
    }
    
    mapping(bytes32 => Certificate) public certificates;
    
    event CertificateIssued(
        bytes32 indexed certificateHash,
        address indexed issuer,
        address indexed student
    );
    
    event CertificateRevoked(bytes32 indexed certificateHash);
    
    function issueCertificate(bytes32 _certificateHash, address _student) public {
        require(certificates[_certificateHash].timestamp == 0, "Certificate already exists");
        
        certificates[_certificateHash] = Certificate({
            certificateHash: _certificateHash,
            issuer: msg.sender,
            student: _student,
            isRevoked: false,
            timestamp: block.timestamp
        });
        
        emit CertificateIssued(_certificateHash, msg.sender, _student);
    }
    
    function verifyCertificate(bytes32 _certificateHash) public view returns (bool, address, address, uint256) {
        Certificate memory cert = certificates[_certificateHash];
        require(cert.timestamp != 0, "Certificate does not exist");
        return (!cert.isRevoked, cert.issuer, cert.student, cert.timestamp);
    }
}
```

---

## API Endpoints

### 1. User Authentication
| Method | Endpoint | Description |
|--------|---------|-------------|
| POST   | `/api/auth/register/` | Register a new user |
| POST   | `/api/auth/login/` | Authenticate user |
| POST   | `/api/auth/logout/` | Log out user |

### 2. Certificate Management
| Method | Endpoint | Description |
|--------|---------|-------------|
| POST   | `/api/certificates/issue/` | Issue a new certificate |
| GET    | `/api/certificates/verify/?hash=<hash>` | Verify a certificate |
| GET    | `/api/certificates/list/` | List all certificates |

---

## Usage Workflow

### 1. Issuing a Certificate
1. University logs in and accesses the dashboard.
2. Enters student details and uploads certificate metadata.
3. Signs transaction via MetaMask.
4. Certificate hash is stored on the blockchain.
5. QR code is generated for verification.

### 2. Verifying a Certificate
1. Users can scan a QR code or enter a certificate hash.
2. System fetches blockchain data.
3. Certificate details are displayed along with verification status.

---

## Security Measures
- **Smart Contract Security**: Uses OpenZeppelin libraries for secure role-based access control.
- **Data Encryption**: Uses IPFS for secure file storage.
- **Tamper-Proof**: Certificates are immutable once issued on the blockchain.
- **Multi-Step Verification**: Requires cryptographic proof before certificate issuance.

---

## Future Enhancements
- **Layer 2 Scaling (Polygon)**: Reduce gas costs and improve efficiency.
- **Integration with Learning Platforms**: Automate certificate issuance.
- **Mobile App**: Enable verification via mobile devices.
- **AI-Based Fraud Detection**: Detect and prevent fake certificates.

---

## Contributors
- **sahil giri** - [GitHub](https://github.com/Sahilgiri49)

---

## License

This project is licensed under the MIT License.
