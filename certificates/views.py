from web3 import Web3
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
import json

w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))

def verify_certificate(request, certificate_hash=None):
    if request.method == 'GET':
        return render(request, 'verify_certificate.html')
        
    if request.method == 'POST':
        try:
            certificate = Certificate.objects.get(certificate_hash=certificate_hash)
            
            # Get transaction details from Ganache
            w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
            tx_hash = certificate.blockchain_tx
            tx_details = w3.eth.get_transaction(tx_hash)
            tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
            
            # Reconstruct original JSON data from hash
            original_data = {
                'student_name': certificate.student.username,
                'course_name': certificate.course_name,
                'issue_date': certificate.issue_date.strftime("%Y-%m-%d %H:%M:%S"),
                'issuer': certificate.university.username,
            }
            
            blockchain_data = {
                'block_number': tx_receipt['blockNumber'],
                'block_hash': tx_receipt['blockHash'].hex(),
                'transaction_hash': tx_hash,
                'from_address': tx_details['from'],
                'to_address': tx_details['to'],
                'gas_used': tx_receipt['gasUsed'],
                'timestamp': w3.eth.get_block(tx_receipt['blockNumber'])['timestamp']
            }
            
            return JsonResponse({
                'status': 'success',
                'certificate_data': original_data,
                'blockchain_data': blockchain_data,
                'is_valid': certificate.verify_on_blockchain()
            })
            
        except Certificate.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Certificate not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

@login_required
def issue_certificate(request):
    if request.user.role not in ['university', 'employer', 'institutional']:
        messages.error(request, "You don't have permission to issue certificates")
        return redirect('certificates:dashboard')

    if request.method == 'POST':
        try:
            # Get form data
            student_name = request.POST.get('student_name')
            course_name = request.POST.get('course_name')
            issue_date = request.POST.get('issue_date')
            certificate_file = request.FILES.get('certificate_file')
            transaction_hash = request.POST.get('transaction_hash')
            certificate_hash = request.POST.get('certificate_hash')

            # Validate file type
            if not certificate_file.name.endswith('.pdf'):
                raise ValueError('Only PDF files are allowed')

            try:
                student = User.objects.get(username=student_name)
            except User.DoesNotExist:
                raise ValueError('Student not found')

            # Save certificate to database
            certificate = Certificate.objects.create(
                student=student,
                university=request.user,
                course_name=course_name,
                completion_date=timezone.now().date(),
                certificate_file=certificate_file,
                blockchain_tx=transaction_hash,
                certificate_hash=certificate_hash,
                status='ISSUED'
            )

            # Get all certificates for this issuer
            certificates = Certificate.objects.filter(
                university=request.user
            ).order_by('-issue_date')

            messages.success(request, 'Certificate issued successfully!')
            return JsonResponse({
                'status': 'success',
                'id': certificate.id,
                'redirect_url': reverse('certificates:dashboard'),
                'certificates': [
                    {
                        'student_name': cert.student.username,
                        'course_name': cert.course_name,
                        'issue_date': cert.issue_date.strftime("%Y-%m-%d %H:%M:%S"),
                        'status': cert.get_status_display(),
                        'certificate_hash': cert.certificate_hash
                    } for cert in certificates
                ]
            })

        except Exception as e:
            messages.error(request, f'Error issuing certificate: {str(e)}')
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return render(request, 'issue_certificate.html')

@login_required
def certificate_list(request):
    if request.user.role == 'university':
        certificates = Certificate.objects.filter(university=request.user)
    elif request.user.role == 'student':
        certificates = Certificate.objects.filter(student=request.user)
    else:
        certificates = Certificate.objects.none()
        
    return render(request, 'certificate_list.html', {
        'certificates': certificates
    })

@login_required
def dashboard(request):
    template_map = {
        'student': 'dashboard/student.html',
        'university': 'dashboard/university.html',
        'employer': 'dashboard/employer.html',
        'institutional': 'dashboard/university.html'  # Institutional users use university template
    }
    template_name = template_map.get(request.user.role, 'dashboard/student.html')
    
    context = {
        'user': request.user,
        'certificates': Certificate.objects.filter(university=request.user) if request.user.role in ['university', 'employer', 'institutional'] else [],
        'can_issue': request.user.role in ['university', 'employer', 'institutional'],
        'role_display': request.user.get_role_display()
    }
    
    return render(request, template_name, context)

@login_required
def verify_document(request, certificate_hash):
    if request.method == 'POST' and request.FILES.get('document'):
        try:
            certificate = Certificate.objects.get(certificate_hash=certificate_hash)
            uploaded_file = request.FILES['document']
            
            # Verify document hash
            is_valid_hash = certificate.verify_document_hash(uploaded_file)
            
            # Verify on blockchain
            is_valid_blockchain = certificate.verify_on_blockchain()
            
            return JsonResponse({
                'status': 'success',
                'is_valid': is_valid_hash and is_valid_blockchain,
                'hash_valid': is_valid_hash,
                'blockchain_valid': is_valid_blockchain,
                'certificate_data': {
                    'student_name': certificate.student.username,
                    'course_name': certificate.course_name,
                    'issue_date': certificate.issue_date.strftime("%Y-%m-%d %H:%M:%S"),
                    'issuer': certificate.university.username
                }
            })
            
        except Certificate.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Certificate not found'
            }, status=404)
            
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request'
    }, status=400) 