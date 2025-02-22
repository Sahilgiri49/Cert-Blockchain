from pymongo import MongoClient
from django.conf import settings
from datetime import datetime

class MongoDBClient:
    def __init__(self):
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client[settings.MONGODB_NAME]
        self.certificate_requests = self.db.certificate_requests

    def store_certificate_request(self, certificate):
        """Store certificate request in MongoDB"""
        request_data = {
            'request_id': certificate.certificate_hash,
            'student': {
                'id': str(certificate.student.id),
                'name': certificate.student.get_full_name(),
                'email': certificate.student.email,
                'student_id': certificate.student_identifier,
                'wallet_address': certificate.wallet_address
            },
            'university': {
                'id': str(certificate.university.id),
                'name': certificate.university.get_full_name(),
                'email': certificate.university.email
            },
            'course': {
                'name': certificate.course_name,
                'completion_date': certificate.completion_date.isoformat()
            },
            'status': certificate.status,
            'verification_status': certificate.verification_status,
            'timestamps': {
                'requested': certificate.request_timestamp.isoformat(),
                'last_updated': datetime.now().isoformat()
            },
            'metadata': {
                'source': 'web_application',
                'blockchain_network': settings.BLOCKCHAIN_NETWORK
            }
        }
        
        return self.certificate_requests.insert_one(request_data)

    def update_request_status(self, request_id, new_status):
        """Update certificate request status"""
        return self.certificate_requests.update_one(
            {'request_id': request_id},
            {
                '$set': {
                    'status': new_status,
                    'timestamps.last_updated': datetime.now().isoformat()
                }
            }
        )

    def get_certificate_request(self, request_id):
        """Retrieve certificate request details"""
        return self.certificate_requests.find_one({'request_id': request_id}) 