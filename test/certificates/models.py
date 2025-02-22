from django.db import models
from django.contrib.auth.models import AbstractUser
from .mongodb import MongoDBClient
import hashlib
from web3 import Web3
from django.conf import settings

# Create your models here.

class User(AbstractUser):
    STUDENT = 'student'
    UNIVERSITY = 'university'
    EMPLOYER = 'employer'
    ADMIN = 'admin'
    
    ROLE_CHOICES = [
        (STUDENT, 'Student'),
        (UNIVERSITY, 'University'),
        (EMPLOYER, 'Employer'),
        (ADMIN, 'Admin'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    wallet_address = models.CharField(max_length=42, unique=True, null=True)
    
class Certificate(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('ISSUED', 'Issued'),
        ('REVOKED', 'Revoked'),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    university = models.ForeignKey(User, on_delete=models.CASCADE, related_name='issued_certificates')
    student_identifier = models.CharField(max_length=50)
    course_name = models.CharField(max_length=200)
    completion_date = models.DateField()
    issue_date = models.DateTimeField(auto_now_add=True)
    certificate_file = models.FileField(upload_to='certificates/', null=True)
    certificate_hash = models.CharField(max_length=66, unique=True)
    blockchain_tx = models.CharField(max_length=66, null=True)
    is_revoked = models.BooleanField(default=False)
    ipfs_hash = models.CharField(max_length=100, null=True)
    qr_code = models.ImageField(upload_to='qr_codes/', null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    request_timestamp = models.DateTimeField(auto_now_add=True)
    wallet_address = models.CharField(max_length=42, null=True)
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending Verification'),
            ('VERIFIED', 'Details Verified'),
            ('FAILED', 'Verification Failed')
        ],
        default='PENDING'
    )
    mongodb_id = models.CharField(max_length=24, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.mongodb_id and self.certificate_hash:
            # Store in MongoDB when first created
            mongo_client = MongoDBClient()
            result = mongo_client.store_certificate_request(self)
            self.mongodb_id = str(result.inserted_id)
        super().save(*args, **kwargs)

    def verify_document_hash(self, uploaded_file):
        """Verify if uploaded document matches stored hash"""
        hasher = hashlib.sha256()
        for chunk in uploaded_file.chunks():
            hasher.update(chunk)
        uploaded_hash = hasher.hexdigest()
        return uploaded_hash == self.certificate_hash

    def verify_on_blockchain(self):
        """Verify certificate on blockchain"""
        w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
        contract = w3.eth.contract(
            address=settings.CONTRACT_ADDRESS,
            abi=settings.CONTRACT_ABI
        )
        try:
            result = contract.functions.verifyCertificate(self.certificate_hash).call()
            return result
        except Exception as e:
            print(f"Blockchain verification error: {e}")
            return False
