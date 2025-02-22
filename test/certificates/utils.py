import hashlib
import json
import requests
from django.conf import settings
import ipfshttpclient
from django.core.exceptions import ValidationError
from .models import Certificate, User
from django.core.mail import send_mail
from django.template.loader import render_to_string

def generate_certificate_hash(certificate_data):
    """Generate a SHA-256 hash of the certificate data"""
    data_string = json.dumps(certificate_data, sort_keys=True)
    return hashlib.sha256(data_string.encode()).hexdigest()

def upload_to_ipfs(file_content):
    """Upload content to IPFS and return the hash"""
    try:
        # Connect to local IPFS daemon
        client = ipfshttpclient.connect(f'/ip4/{settings.IPFS_HOST}/tcp/{settings.IPFS_PORT}')
        
        # Add the content to IPFS
        if isinstance(file_content, str):
            file_content = file_content.encode()
        
        result = client.add_bytes(file_content)
        return result['Hash']
    except Exception as e:
        print(f"Error uploading to IPFS: {str(e)}")
        return None
    finally:
        if 'client' in locals():
            client.close()

def verify_certificate_hash(certificate_hash, certificate_data):
    """Verify if the provided hash matches the certificate data"""
    computed_hash = generate_certificate_hash(certificate_data)
    return computed_hash == certificate_hash 

def verify_student_details(student, university_id, student_id, full_name):
    """
    Verify student details against university records
    Returns (bool, str) tuple - (is_valid, error_message)
    """
    try:
        university = User.objects.get(id=university_id, role='university')
        
        # Check if student is enrolled in the university
        # This assumes there's a relationship between students and universities
        if not university.enrolled_students.filter(id=student.id).exists():
            return False, "Student is not enrolled in the selected university"
            
        # Verify student ID matches university records
        if student.student_identifier != student_id:
            return False, "Student ID does not match university records"
            
        # Verify full name matches records
        if student.full_name.lower() != full_name.lower():
            return False, "Student name does not match university records"
            
        return True, ""
        
    except User.DoesNotExist:
        return False, "Invalid university selected" 

def notify_university_admin(certificate):
    """Send notification to university admin about new certificate request"""
    
    # Email context
    context = {
        'student_name': certificate.student.get_full_name(),
        'student_id': certificate.student_identifier,
        'course_name': certificate.course_name,
        'request_id': certificate.certificate_hash,
        'request_date': certificate.request_timestamp
    }
    
    # Render email content from template
    email_html = render_to_string('emails/new_certificate_request.html', context)
    email_text = render_to_string('emails/new_certificate_request.txt', context)
    
    # Send email to university admin
    send_mail(
        subject='New Certificate Request Pending Approval',
        message=email_text,
        html_message=email_html,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[certificate.university.email],
        fail_silently=False
    ) 