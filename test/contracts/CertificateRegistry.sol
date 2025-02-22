// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

contract CertificateRegistry is AccessControl, Pausable {
    using Counters for Counters.Counter;
    
    bytes32 public constant UNIVERSITY_ROLE = keccak256("UNIVERSITY_ROLE");
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    
    struct Certificate {
        bytes32 certificateHash;
        address issuer;
        address student;
        bool isRevoked;
        uint256 timestamp;
        string metadataURI;  // IPFS hash for additional data
    }
    
    mapping(bytes32 => Certificate) public certificates;
    mapping(address => bool) public universities;
    Counters.Counter private _certificateCounter;
    
    event CertificateIssued(
        bytes32 indexed certificateHash,
        address indexed issuer,
        address indexed student,
        string metadataURI
    );
    
    event CertificateRevoked(
        bytes32 indexed certificateHash,
        address indexed revokedBy,
        uint256 timestamp
    );
    
    event UniversityAdded(address university);
    event UniversityRemoved(address university);
    
    constructor() {
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _setupRole(ADMIN_ROLE, msg.sender);
    }
    
    modifier onlyUniversity() {
        require(hasRole(UNIVERSITY_ROLE, msg.sender), "Caller is not a university");
        _;
    }
    
    function addUniversity(address university) public onlyRole(ADMIN_ROLE) {
        grantRole(UNIVERSITY_ROLE, university);
        universities[university] = true;
        emit UniversityAdded(university);
    }
    
    function removeUniversity(address university) public onlyRole(ADMIN_ROLE) {
        revokeRole(UNIVERSITY_ROLE, university);
        universities[university] = false;
        emit UniversityRemoved(university);
    }
    
    function issueCertificate(
        bytes32 _certificateHash, 
        address _student,
        string memory _metadataURI
    ) 
        public 
        onlyUniversity 
        whenNotPaused 
    {
        require(certificates[_certificateHash].timestamp == 0, "Certificate already exists");
        require(_student != address(0), "Invalid student address");
        
        certificates[_certificateHash] = Certificate({
            certificateHash: _certificateHash,
            issuer: msg.sender,
            student: _student,
            isRevoked: false,
            timestamp: block.timestamp,
            metadataURI: _metadataURI
        });
        
        _certificateCounter.increment();
        emit CertificateIssued(_certificateHash, msg.sender, _student, _metadataURI);
    }
    
    function verifyCertificate(bytes32 _certificateHash) 
        public 
        view 
        returns (
            bool isValid,
            address issuer,
            address student,
            uint256 timestamp,
            string memory metadataURI
        ) 
    {
        Certificate memory cert = certificates[_certificateHash];
        require(cert.timestamp != 0, "Certificate does not exist");
        
        return (
            !cert.isRevoked,
            cert.issuer,
            cert.student,
            cert.timestamp,
            cert.metadataURI
        );
    }
    
    function revokeCertificate(bytes32 _certificateHash) 
        public 
    {
        require(
            hasRole(ADMIN_ROLE, msg.sender) || 
            certificates[_certificateHash].issuer == msg.sender,
            "Not authorized to revoke"
        );
        require(certificates[_certificateHash].timestamp != 0, "Certificate does not exist");
        require(!certificates[_certificateHash].isRevoked, "Certificate already revoked");
        
        certificates[_certificateHash].isRevoked = true;
        emit CertificateRevoked(_certificateHash, msg.sender, block.timestamp);
    }
    
    function getCertificateCount() public view returns (uint256) {
        return _certificateCounter.current();
    }
    
    function pause() public onlyRole(ADMIN_ROLE) {
        _pause();
    }
    
    function unpause() public onlyRole(ADMIN_ROLE) {
        _unpause();
    }
} 