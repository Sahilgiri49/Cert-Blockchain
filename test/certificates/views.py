from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, Certificate
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.crypto import get_random_string
from .utils import generate_certificate_hash, upload_to_ipfs, verify_student_details, notify_university_admin
import json
from django.http import JsonResponse
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import uuid
from .mongodb import MongoDBClient

# 
from django.http import JsonResponse
from rest_framework.decorators import api_view
from .services.ipfs_service import upload_to_ipfs, get_from_ipfs

@api_view(['POST'])
def upload_file(request):
    file = request.FILES.get("file")
    if not file:
        return JsonResponse({"error": "No file provided"}, status=400)

    file_path = f"temp/{file.name}"
    with open(file_path, "wb+") as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    ipfs_hash = upload_to_ipfs(file_path)
    if ipfs_hash:
        return JsonResponse({"ipfs_hash": ipfs_hash, "url": get_from_ipfs(ipfs_hash)})
    else:
        return JsonResponse({"error": "Failed to upload"}, status=500)

@api_view(['GET'])
def get_file(request, cid):
    return JsonResponse({"url": get_from_ipfs(cid)})
# 

def home(request):
    return render(request, 'home.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_role_display()}!')
                return redirect('certificates:dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email.')
    
    return render(request, 'auth/login.html')

@ensure_csrf_cookie
def register(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'auth/register.html')
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role=role
            )
            login(request, user)
            messages.success(request, f'Account created successfully as {user.get_role_display()}!')
            return redirect('certificates:dashboard')
        except Exception as e:
            messages.error(request, str(e))
    
    return render(request, 'auth/register.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('certificates:home')

def verify_certificate(request):
    # Allow access to everyone, even unauthenticated users
    return render(request, 'verify_certificate.html')

@login_required
def issue_certificate(request):
    if request.user.role not in ['university', 'employer']:
        messages.error(request, "You don't have permission to issue certificates")
        return redirect('certificates:dashboard')

    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        course_name = request.POST.get('course_name')
        issue_date = request.POST.get('issue_date')
        certificate_file = request.FILES.get('certificate_file')

        certificate_hash = get_random_string(64)

        try:
            student = User.objects.get(username=student_name)
            certificate = Certificate.objects.create(
                student=student,
                university=request.user,
                course_name=course_name,
                issue_date=issue_date,
                certificate_file=certificate_file,
                certificate_hash=certificate_hash
            )
            messages.success(request, 'Certificate issued successfully!')
            return redirect('certificates:dashboard')
        except User.DoesNotExist:
            messages.error(request, 'Student not found.')
            return redirect('certificates:issue')

    return render(request, 'issue_certificate.html')

@login_required
def dashboard(request):
    if request.user.role == 'university':
        pending_requests = Certificate.objects.filter(
            university=request.user,
            status='PENDING'
        ).select_related('student').order_by('-request_timestamp')
        
        return render(request, 'dashboard/university.html', {
            'pending_requests': pending_requests
        })
    
    template_map = {
        'student': 'dashboard/student.html',
        'university': 'dashboard/university.html',
        'employer': 'dashboard/employer.html'
    }
    template_name = template_map.get(request.user.role, 'dashboard/student.html')
    
    context = {
        'user': request.user,
        'certificates': [],  # Add your certificates queryset here
        'can_issue': request.user.role in ['university', 'employer'],
        'role_display': request.user.get_role_display()
    }
    
    return render(request, template_name, context)

@login_required
def view_certificate(request, hash):
    try:
        certificate = Certificate.objects.get(certificate_hash=hash)
        return render(request, 'view_certificate.html', {'certificate': certificate})
    except Certificate.DoesNotExist:
        messages.error(request, 'Certificate not found.')
        return redirect('certificates:dashboard')

@login_required
def request_certificate(request):
    if request.user.role != 'student':
        messages.error(request, "Only students can request certificates")
        return redirect('certificates:dashboard')

    if not request.user.wallet_address:
        messages.warning(request, "Please register your MetaMask wallet first")
        return redirect('certificates:register_wallet')

    if request.method == 'POST':
        wallet_address = request.POST.get('wallet_address')
        university_id = request.POST.get('university')
        student_id = request.POST.get('student_id')
        full_name = request.POST.get('full_name')
        course_name = request.POST.get('course_name')
        completion_date = request.POST.get('completion_date')
        
        # Verify wallet address
        if wallet_address != request.user.wallet_address:
            messages.error(request, "Please use your registered wallet address")
            return redirect('certificates:request')

        # Verify student details
        is_valid, error_message = verify_student_details(
            request.user, 
            university_id, 
            student_id, 
            full_name
        )
        
        if not is_valid:
            messages.error(request, error_message)
            return redirect('certificates:request')

        # Check for duplicate requests
        duplicate_request = Certificate.objects.filter(
            student=request.user,
            university_id=university_id,
            course_name=course_name,
            status__in=['PENDING', 'APPROVED', 'ISSUED']
        ).exists()

        if duplicate_request:
            messages.error(request, "A certificate request already exists for this course at the selected university")
            return redirect('certificates:request')

        try:
            # Generate unique request ID and create certificate
            request_id = str(uuid.uuid4())
            
            certificate = Certificate.objects.create(
                student=request.user,
                university_id=university_id,
                student_identifier=student_id,
                course_name=course_name,
                completion_date=completion_date,
                status='PENDING',
                wallet_address=wallet_address,
                certificate_hash=request_id,
                verification_status='PENDING'
            )
            
            # Store in MongoDB
            mongo_client = MongoDBClient()
            mongo_client.store_certificate_request(certificate)
            
            # Notify university admin
            notify_university_admin(certificate)
            
            # Send confirmation email to student
            send_mail(
                'Certificate Request Submitted',
                f'Your certificate request (ID: {request_id}) has been submitted and is pending approval.',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=False,
            )
            
            messages.success(request, f'Certificate request submitted successfully! Request ID: {request_id}')
            return redirect('certificates:dashboard')
            
        except Exception as e:
            messages.error(request, f'Error submitting request: {str(e)}')
            return redirect('certificates:request')

    return render(request, 'request_certificate.html')

@login_required
def approve_certificate(request, certificate_id):
    if request.user.role != 'university':
        messages.error(request, "Only universities can approve certificates")
        return redirect('certificates:dashboard')

    try:
        certificate = Certificate.objects.get(id=certificate_id)
        
        # Generate certificate file and hash
        certificate_data = {
            'student_name': certificate.student.username,
            'student_id': certificate.student_id,
            'course_name': certificate.course_name,
            'completion_date': str(certificate.completion_date),
            'university': certificate.university.username
        }
        
        # Upload to IPFS
        ipfs_hash = upload_to_ipfs(json.dumps(certificate_data))
        
        # Update certificate
        certificate.status = 'APPROVED'
        certificate.ipfs_hash = ipfs_hash
        certificate.save()
        
        messages.success(request, 'Certificate approved successfully!')
    except Certificate.DoesNotExist:
        messages.error(request, 'Certificate not found')
    
    return redirect('certificates:dashboard')

@login_required
def verify_wallet(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        wallet_address = data.get('wallet_address')
        
        # Check if wallet is registered to the current user
        is_registered = (
            request.user.wallet_address is not None and 
            request.user.wallet_address.lower() == wallet_address.lower()
        )
        
        return JsonResponse({
            'is_registered': is_registered
        })
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def approve_request(request, certificate_id):
    if request.user.role != 'university':
        messages.error(request, "Only universities can approve/reject certificates")
        return redirect('certificates:dashboard')

    try:
        certificate = Certificate.objects.get(id=certificate_id, university=request.user)
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'approve':
                # Update certificate status
                certificate.status = 'APPROVED'
                certificate.save()
                
                # Notify student
                send_mail(
                    'Certificate Request Approved',
                    'Your certificate request has been approved and will be issued shortly.',
                    settings.DEFAULT_FROM_EMAIL,
                    [certificate.student.email],
                    fail_silently=False,
                )
                
                messages.success(request, 'Certificate request approved successfully')
                
            elif action == 'reject':
                reason = request.POST.get('rejection_reason')
                certificate.status = 'REJECTED'
                certificate.save()
                
                # Notify student with rejection reason
                send_mail(
                    'Certificate Request Rejected',
                    f'Your certificate request has been rejected.\nReason: {reason}',
                    settings.DEFAULT_FROM_EMAIL,
                    [certificate.student.email],
                    fail_silently=False,
                )
                
                messages.success(request, 'Certificate request rejected')
                
        return redirect('certificates:dashboard')
        
    except Certificate.DoesNotExist:
        messages.error(request, 'Certificate request not found')
        return redirect('certificates:dashboard')

def certificate_list(request):
    certificates = Certificate.objects.filter(issuer=request.user)
    return render(request, 'certificate_list.html', {
        'certificates': certificates
    })
