from django.urls import path
from . import views
from .views import upload_file, get_file
from web3 import Web3
from django.http import JsonResponse

app_name = 'certificates'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('verify/', views.verify_certificate, name='verify'),
    path('issue/', views.issue_certificate, name='issue'),
    path('certificate/<str:hash>/', views.view_certificate, name='view_certificate'),
    path("upload/", upload_file, name="upload"),
    path("file/<str:cid>/", get_file, name="get_file"),
    path('list/', views.certificate_list, name='list'),
    path('verify/<str:certificate_hash>/', views.verify_certificate, name='verify_certificate'),
] 

def verify_certificate(request, certificate_hash=None):
    if request.method == 'GET':
        return render(request, 'verify_certificate.html')
        
    if request.method == 'POST':
        try:
            # Get certificate from database
            certificate = Certificate.objects.get(certificate_hash=certificate_hash)
            
            # Verify document hash if file uploaded
            is_valid_hash = True
            if 'document' in request.FILES:
                is_valid_hash = certificate.verify_document_hash(request.FILES['document'])
            
            # Verify on blockchain
            w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
            contract = w3.eth.contract(
                address=settings.CONTRACT_ADDRESS,
                abi=settings.CONTRACT_ABI
            )
            blockchain_result = contract.functions.verifyCertificate(
                Web3.toBytes(hexstr=certificate_hash)
            ).call()
            
            return JsonResponse({
                'status': 'success',
                'is_valid': is_valid_hash and blockchain_result[0],
                'hash_valid': is_valid_hash,
                'blockchain_valid': blockchain_result[0],
                'certificate_data': {
                    'student_name': certificate.student.username,
                    'course_name': certificate.course_name,
                    'issue_date': certificate.issue_date.strftime("%Y-%m-%d %H:%M:%S"),
                    'issuer': certificate.university.username,
                    'blockchain_tx': certificate.blockchain_tx
                }
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