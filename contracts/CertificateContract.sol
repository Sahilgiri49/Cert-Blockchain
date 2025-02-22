// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract CertificateContract {
    struct Certificate {
        bytes32 hash;
        address issuer;
        uint256 timestamp;
        bool isValid;
    }
    
    mapping(bytes32 => Certificate) public certificates;
    
    event CertificateIssued(bytes32 indexed hash, address indexed issuer);
    event CertificateRevoked(bytes32 indexed hash, address indexed issuer);
    
    function issueCertificate(bytes32 _hash) public {
        require(certificates[_hash].timestamp == 0, "Certificate already exists");
        
        certificates[_hash] = Certificate({
            hash: _hash,
            issuer: msg.sender,
            timestamp: block.timestamp,
            isValid: true
        });
        
        emit CertificateIssued(_hash, msg.sender);
    }
    
    function verifyCertificate(bytes32 _hash) public view returns (bool, address, uint256) {
        Certificate memory cert = certificates[_hash];
        return (cert.isValid, cert.issuer, cert.timestamp);
    }
    
    function revokeCertificate(bytes32 _hash) public {
        require(certificates[_hash].issuer == msg.sender, "Only issuer can revoke");
        certificates[_hash].isValid = false;
        emit CertificateRevoked(_hash, msg.sender);
    }
} 