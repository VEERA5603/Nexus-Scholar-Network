# views.py
from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError
from ..models import BriefDetails, PersonalInformation,Hosteller,BankDetails
from datetime import datetime
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

@method_decorator(ensure_csrf_cookie, name='dispatch')
class BreifView(View):
    authentication_classes = []
    permission_classes = [AllowAny]
    session_manager = SessionManager()

    def get_context(self, user):
        breif_data = BriefDetails.objects.filter(roll_number__roll_number=user.username).first()
        return {
            'breif_data': breif_data,
            'roll_number': user.username
        }

    def get(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return redirect('student-login')
        
        try:
            session = SessionManager().get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
            
            user = get_user_model().objects.get(id=session.user_id)
            if session.user_type != 'student':
                return HttpResponse('Unauthorized', status=403)
            
            context = self.get_context(user)
            if request.headers.get('HX-Request'):
                return render(request, 'Student Details/breif/breif_form.html', context)
            return render(request, 'Student Details/breif/breif_details.html', context)
            
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            response = redirect('student-login')
            response.delete_cookie('session_id')
            return response

    def post(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return HttpResponse('Unauthorized', status=401)

        try:
            session = SessionManager().get_session(session_id)
            user = get_user_model().objects.get(id=session.user_id)
            personal_info = PersonalInformation.objects.get(roll_number=user.username)

            breif_data = {
                'roll_number': personal_info,
                'identification_marks': request.POST.get('identification_marks'),
                'extracurricular_activities': request.POST.get('extracurricular_activities'),
                'brother_name': request.POST.get('brother_name'),
                'brother_mobile': request.POST.get('sister_names'),
                'sister_names': request.POST.get('sister_names'),
                'sister_mobile': request.POST.get('sister_mobile'),
                'friends_names': request.POST.get('friends_names'),
                'friends_mobile': request.POST.get('friends_mobile'),
                'having_vehicle': request.POST.get('having_vehicle') == 'true',
                'friends_mobile': request.POST.get('friends_mobile'),
                'vehicle_number': request.POST.get('vehicle_number'),
                'hobbies': request.POST.get('hobbies'),
            }

            briefdetails, created = BriefDetails.objects.update_or_create(
                roll_number=personal_info,
                defaults=breif_data
            )

            context = self.get_context(user)
            context['message'] = 'Breif information saved successfully!'
            return render(request, 'Student Details/breif/breif_form.html', context)

        except (ValidationError, ValueError) as e:
            return HttpResponse(str(e), status=400)
        except Exception as e:
            return HttpResponse('An error occurred', status=500)
        


@method_decorator(ensure_csrf_cookie, name='dispatch')
class HostellarView(View):
    authentication_classes = []
    permission_classes = [AllowAny]
    session_manager = SessionManager()

    def get_context(self, user):
        host_data = Hosteller.objects.filter(roll_number__roll_number=user.username).first()
        return {
            'host_data': host_data,
            'roll_number': user.username
        }

    def get(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return redirect('student-login')
        
        try:
            session = SessionManager().get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
            
            user = get_user_model().objects.get(id=session.user_id)
            if session.user_type != 'student':
                return HttpResponse('Unauthorized', status=403)
            
            context = self.get_context(user)
            if request.headers.get('HX-Request'):
                return render(request, 'Student Details/Hostellar/host_form.html', context)
            return render(request, 'Student Details/Hostellar/host_details.html', context)
            
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            response = redirect('student-login')
            response.delete_cookie('session_id')
            return response

    def post(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return HttpResponse('Unauthorized', status=401)

        try:
            session = SessionManager().get_session(session_id)
            user = get_user_model().objects.get(id=session.user_id)
            personal_info = PersonalInformation.objects.get(roll_number=user.username)

            host_data = {
                'roll_number': personal_info,
                'first_name': request.POST.get('first_name'),
                'last_name': request.POST.get('last_name'),
                'hostel_name': request.POST.get('hostel_name'),
                'hostel_address': request.POST.get('hostel_address'),
                'from_date': request.POST.get('from_date'),
                'to_date': request.POST.get('to_date'),
                'room_number': request.POST.get('room_number'),
            }

            hostellar, created = Hosteller.objects.update_or_create(
                roll_number=personal_info,
                defaults=host_data
            )

            context = self.get_context(user)
            context['message'] = 'Hostel information saved successfully!'
            return render(request, 'Student Details/Hostellar/host_form.html', context)

        except (ValidationError, ValueError) as e:
            return HttpResponse(str(e), status=400)
        except Exception as e:
            return HttpResponse('An error occurred', status=500)
        


@method_decorator(ensure_csrf_cookie, name='dispatch')
class BankView(View):
    authentication_classes = []
    permission_classes = [AllowAny]
    session_manager = SessionManager()

    def get_context(self, user):
        bank_data = BankDetails.objects.filter(roll_number__roll_number=user.username).first()
        return {
            'bank_data': bank_data,
            'roll_number': user.username
        }

    def get(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return redirect('student-login')
        
        try:
            session = SessionManager().get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
            
            user = get_user_model().objects.get(id=session.user_id)
            if session.user_type != 'student':
                return HttpResponse('Unauthorized', status=403)
            
            context = self.get_context(user)
            if request.headers.get('HX-Request'):
                return render(request, 'Student Details/bank/bank_form.html', context)
            return render(request, 'Student Details/bank/bank_details.html', context)
            
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            response = redirect('student-login')
            response.delete_cookie('session_id')
            return response

    def post(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return HttpResponse('Unauthorized', status=401)

        try:
            session = SessionManager().get_session(session_id)
            user = get_user_model().objects.get(id=session.user_id)
            personal_info = PersonalInformation.objects.get(roll_number=user.username)

            bank_data = {
                'roll_number': personal_info,
                'first_name': request.POST.get('first_name'),
                'last_name': request.POST.get('last_name'),
                'account_number': request.POST.get('account_number'),
                'branch': request.POST.get('branch'),
                'ifsc': request.POST.get('ifsc'),
                'micr': request.POST.get('micr'),
                'account_type': request.POST.get('account_type'),
                'address': request.POST.get('address'),
                'pan_number': request.POST.get('pan_number'),
            }
    
            academics, created = BankDetails.objects.update_or_create(
                roll_number=personal_info,
                defaults=bank_data
            )

            context = self.get_context(user)
            context['message'] = 'BANK information saved successfully!'
            return render(request, 'Student Details/bank/bank_form.html', context)

        except (ValidationError, ValueError) as e:
            return HttpResponse(str(e), status=400)
        except Exception as e:
            return HttpResponse('An error occurred', status=500)
        

