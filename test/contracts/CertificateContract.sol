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
        
        return (
            !cert.isRevoked,
            cert.issuer,
            cert.student,
            cert.timestamp
        );
    }
    
    function revokeCertificate(bytes32 _certificateHash) public {
        require(certificates[_certificateHash].timestamp != 0, "Certificate does not exist");
        require(certificates[_certificateHash].issuer == msg.sender, "Only issuer can revoke");
        
        certificates[_certificateHash].isRevoked = true;
        emit CertificateRevoked(_certificateHash);
    }
} 