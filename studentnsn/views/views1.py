from django.views import View
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError
from django.db import transaction
import jwt
from django.conf import settings
from ..models import PersonalInformation, Address
from authnsn.models import Student
from rest_framework_simplejwt.authentication import JWTAuthentication
import logging
from ..models import PersonalInformation, Address
from authnsn.models import Student
from authnsn.session_manager import SessionManager


class AddressView(APIView):
    @method_decorator(csrf_protect)
    def post(self, request):
        try:
            address_data = {
                'area_type': request.POST.get('area_type'),
                'door_number': request.POST.get('door_number'),
                'apartment_name': request.POST.get('apartment_name'),
                'street_name': request.POST.get('street_name'),
                'taluk': request.POST.get('taluk'),
                'block': request.POST.get('block'),
                'district': request.POST.get('district'),
                'state': request.POST.get('state'),
                'pincode': request.POST.get('pincode')
            }
            
            address = Address.objects.create(**address_data)
            return JsonResponse({'id': address.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


logger = logging.getLogger(__name__)

@method_decorator(csrf_protect, name='dispatch')
class PersonalInformationView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    session_manager = SessionManager()

    def get_student_from_token(self, request):
        session_id = request.COOKIES.get('session_id')
        
        if not session_id:
            return redirect('student-login')
        
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
            user = get_user_model().objects.get(id=session.user_id)
            return user, Student.objects.filter(roll_number=user.username).first()
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return None, None

    def get(self, request):
        try:
            user, student_data = self.get_student_from_token(request)
            if not user or not student_data:
                return redirect('home')

            personal_info = PersonalInformation.objects.filter(
                roll_number=student_data.roll_number
            ).select_related('permanent_address', 'communication_address').first()

            context = {
                'user_type': 'student',
                'roll_number': student_data.roll_number,
                'student_type': student_data.student_type,
                'email': student_data.email,
                'name': student_data.name if hasattr(student_data, 'name') else None,
                'personal_info': personal_info,
            }
            return render(request, 'Student Details/personal/personal_information.html', context)
        except Exception as e:
            logger.error(f"GET request error: {str(e)}")
            return HttpResponse("An error occurred", status=500)

    @transaction.atomic
    def post(self, request):
        try:
            user, student_data = self.get_student_from_token(request)
            if not user or not student_data:
                return HttpResponse('Unauthorized', status=401)

            # Log received data for debugging
            logger.debug(f"Received POST data: {request.POST}")

            # Handle permanent address
            perm_address_data = {
                'area_type': request.POST.get('permanent_area_type'),
                'door_number': request.POST.get('permanent_door_number'),
                'apartment_name': request.POST.get('permanent_apartment_name', ''),  # Make optional
                'street_name': request.POST.get('permanent_street_name'),
                'taluk': request.POST.get('permanent_taluk', ''),  # Make optional
                'block': request.POST.get('permanent_block', ''),  # Make optional
                'district': request.POST.get('permanent_district'),
                'state': request.POST.get('permanent_state'),
                'pincode': request.POST.get('permanent_pincode')
            }

            # Clean the data
            perm_address_data = {k: v.strip() if isinstance(v, str) else v 
                               for k, v in perm_address_data.items() if v}

            # Create permanent address
            permanent_address = Address.objects.create(**perm_address_data)

            # Handle communication address
            same_as_permanent = request.POST.get('same_as_permanent') == 'true'
            if same_as_permanent:
                communication_address = permanent_address
            else:
                comm_address_data = {
                    'area_type': request.POST.get('communication_area_type'),
                    'door_number': request.POST.get('communication_door_number'),
                    'apartment_name': request.POST.get('communication_apartment_name', ''),
                    'street_name': request.POST.get('communication_street_name'),
                    'taluk': request.POST.get('communication_taluk', ''),
                    'block': request.POST.get('communication_block', ''),
                    'district': request.POST.get('communication_district'),
                    'state': request.POST.get('communication_state'),
                    'pincode': request.POST.get('communication_pincode')
                }
                comm_address_data = {k: v.strip() if isinstance(v, str) else v 
                                   for k, v in comm_address_data.items() if v}
                communication_address = Address.objects.create(**comm_address_data)

            # Prepare personal information data
            personal_info_data = {
                'roll_number': student_data.roll_number,
                'type_of_student': int(request.POST.get('type_of_student', 0)),
                'first_name': request.POST.get('first_name', '').strip(),
                'last_name': request.POST.get('last_name', '').strip(),
                'dob': request.POST.get('dob'),
                'gender': request.POST.get('gender'),
                'blood_group': request.POST.get('blood_group', '').strip(),
                'religion': request.POST.get('religion', '').strip(),
                'community': request.POST.get('community', '').strip(),
                'caste': request.POST.get('caste', '').strip(),
                'nationality': request.POST.get('nationality', '').strip(),
                'student_mobile': request.POST.get('student_mobile'),
                'email': request.POST.get('email', '').strip(),
                'aadhar_number': request.POST.get('aadhar_number'),
                'father_name': request.POST.get('father_name', '').strip(),
                'father_occupation': request.POST.get('father_occupation', '').strip(),
                'mother_name': request.POST.get('mother_name', '').strip(),
                'mother_occupation': request.POST.get('mother_occupation', '').strip(),
                'father_mobile': request.POST.get('father_mobile'),
                'mother_mobile': request.POST.get('mother_mobile'),
                'annual_income': float(request.POST.get('annual_income', 0)),
                'height': float(request.POST.get('height', 0)),
                'weight': float(request.POST.get('weight', 0)),
                'differentially_abled': request.POST.get('differentially_abled') == 'true',
                'Type_of_disability': request.POST.get('Type_of_disability'),
                'special_quota': request.POST.get('special_quota', '0'),
                'permanent_address': permanent_address,
                'communication_address': communication_address,
            }

            # Handle optional previous_roll_number
            prev_roll = request.POST.get('previous_roll_number')
            if prev_roll:
                personal_info_data['previous_roll_number'] = prev_roll

            # Create or update personal information
            personal_info, created = PersonalInformation.objects.update_or_create(
                roll_number=student_data.roll_number,
                defaults=personal_info_data
            )

            success_message = 'Personal information saved successfully!'
            if request.headers.get('HX-Request'):
                return HttpResponse(
                    f'<div class="alert alert-success">{success_message}</div>',
                    headers={'HX-Trigger': 'personalInfoSaved'}
                )
            return JsonResponse({'message': success_message})

        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            error_message = str(e)
            if request.headers.get('HX-Request'):
                return HttpResponse(
                    f'<div class="alert alert-danger">{error_message}</div>',
                    status=400
                )
            return JsonResponse({'error': error_message}, status=400)
            
        except Exception as e:
            logger.error(f"POST request error: {str(e)}")
            error_message = 'An error occurred while saving the data.'
            if request.headers.get('HX-Request'):
                return HttpResponse(
                    f'<div class="alert alert-danger">{error_message}</div>',
                    status=500
                )
            return JsonResponse({'error': error_message}, status=500)
        
@method_decorator(csrf_protect, name='dispatch')
class CopyAddressView(View):
    def post(self, request):
        if request.headers.get('HX-Request'):
            # Return empty communication address fields if unchecked
            if request.POST.get('same_as_permanent') != 'true':
                return render(request, 'partials/communication_address_fields.html', {'disabled': False})
            
            # Get permanent address values from form
            permanent_data = {
                'area_type': request.POST.get('permanent_area_type'),
                'door_number': request.POST.get('permanent_door_number'),
                'apartment_name': request.POST.get('permanent_apartment_name'),
                'street_name': request.POST.get('permanent_street_name'),
                'taluk': request.POST.get('permanent_taluk'),
                'block': request.POST.get('permanent_block'),
                'district': request.POST.get('permanent_district'),
                'state': request.POST.get('permanent_state'),
                'pincode': request.POST.get('permanent_pincode')
            }
            
            # Return communication address fields with permanent address values
            return render(request, 'partials/communication_address_fields.html', {
                'address': permanent_data,
                'disabled': True
            })
        
        return HttpResponse(status=400)

@method_decorator(csrf_protect, name='dispatch')
class GetPersonalInfoView(View):
    def get(self, request, roll_number):
        try:
            personal_info = PersonalInformation.objects.select_related(
                'permanent_address', 
                'communication_address'
            ).get(roll_number=roll_number)
            
            data = {
                'personal_info': personal_info,
                'permanent_address': personal_info.permanent_address,
                'communication_address': personal_info.communication_address,
                'same_as_permanent': (
                    personal_info.permanent_address.id == 
                    personal_info.communication_address.id
                )
            }
            
            if request.headers.get('HX-Request'):
                return render(request, 'partials/personal_info_form.html', data)
            return JsonResponse(data)
            
        except PersonalInformation.DoesNotExist:
            if request.headers.get('HX-Request'):
                return HttpResponse(
                    '<div class="alert alert-warning">No personal information found.</div>',
                    status=404
                )
            return JsonResponse({'error': 'Not found'}, status=404)