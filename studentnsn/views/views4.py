from django.views import View
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.db.models import Avg, F
from decimal import Decimal
from django.middleware.csrf import get_token
from django.http import HttpResponse, FileResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_protect
from django.core.files.storage import default_storage
from django.urls import path
import os
from django.db import models
from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError
from ..models import Academics, PersonalInformation, SemesterMarksheet,DiplomaMarksheet
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
from ..models import PersonalDocuments
import mimetypes
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.files.storage import default_storage
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from ..models import PersonalDocuments, PersonalInformation
from authnsn.session_manager import SessionManager
import os
import mimetypes
import jwt
from django.contrib.auth import get_user_model
from ..models import Examination
from django.views import View
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from decimal import Decimal
from django.views import View
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.contrib.auth import get_user_model
import jwt

@method_decorator(ensure_csrf_cookie, name='dispatch')
class ExaminationView(View):
    authentication_classes = []
    permission_classes = [AllowAny]
    session_manager = SessionManager()

    def calculate_gpa(self, grades):
        """Calculate GPA from a queryset of grades"""
        total_credits = sum(float(grade.credit_hours) for grade in grades)
        total_points = sum(float(grade.credit_point) for grade in grades)
        return round(total_points / total_credits, 2) if total_credits else 0

    def get(self, request):
        """Handle GET requests to display examination records"""
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return redirect('student-login')
        
        try:
            # Verify session
            session = SessionManager().get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()

            user = get_user_model().objects.get(id=session.user_id)
            
            if session.user_type == 'student':
                student_data = Student.objects.filter(roll_number=user.username).first()
                if student_data:
                    # Get academic records
                    academics = Examination.objects.filter(
                        roll_number=student_data.roll_number
                    ).order_by('semester')
                    
                    # Calculate semester-wise GPA
                    semesters = {}
                    for academic in academics:
                        if academic.semester not in semesters:
                            semester_grades = academics.filter(semester=academic.semester)
                            semesters[academic.semester] = {
                                'grades': semester_grades,
                                'gpa': self.calculate_gpa(semester_grades)
                            }
                    
                    # Calculate CGPA
                    cgpa = self.calculate_gpa(academics) if academics else 0
                    
                    # Get register number from the first academic record or None
                    register_number = academics.first().register_number if academics.exists() else None
                    
                    context = {
                        'user_type': 'student',
                        'roll_number': student_data.roll_number,
                        'register_number': register_number,
                        'semesters': semesters,
                        'cgpa': cgpa,
                        'personal_info': student_data,
                        'csrf_token': get_token(request),  # Explicitly include CSRF token
                    }
                    
                    if request.headers.get('HX-Request'):
                        return render(request, 'Examination/academic_records_partial.html', context)
                    return render(request, 'Examination/examination.html', context)

            return HttpResponse('Unauthorized', status=403)
            
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            response = redirect('student-login')
            response.delete_cookie('session_id')
            return response

    def post(self, request):
        """Handle POST requests to add new examination records"""
        if not request.headers.get('HX-Request'):
            return HttpResponse('Bad Request', status=400)

        # Verify CSRF token
        if not request.POST.get('csrfmiddlewaretoken'):
            return HttpResponse('CSRF token missing', status=403)

        try:
            # Extract form data
            roll_number = request.POST.get('roll_number')
            semester = request.POST.get('semester')
            course_code = request.POST.get('course_code')
            register_number = request.POST.get('register_number')
            
            # Validate register number
            if not register_number:
                return HttpResponse('Register number is required', status=400)
            
            # Calculate grade point based on grade
            grade = request.POST.get('grade')
            grade_points = {
                'S': 10, 'A': 9, 'B': 8, 'C': 7,
                'D': 6, 'E': 5, 'RA': 0, 'AB': 0
            }
            grade_point = grade_points.get(grade, 0)
            credit_hours = Decimal(request.POST.get('credit_hours', 0))
            credit_point = grade_point * credit_hours

            # Create new academic record
            academic = Examination.objects.create(
                roll_number=roll_number,
                register_number=register_number,
                semester=semester,
                course_code=course_code,
                course_name=request.POST.get('course_name'),
                internal_mark=request.POST.get('internal_mark'),
                grade=grade,
                credit_hours=credit_hours,
                grade_point=grade_point,
                credit_point=credit_point,
                exam_held_on=request.POST.get('exam_held_on'),
                regulations=request.POST.get('regulations'),
            )

            # Fetch updated records and return the partial template
            academics = Examination.objects.filter(
                roll_number=roll_number
            ).order_by('semester')
            
            # Calculate semester-wise GPA
            semesters = {}
            for academic in academics:
                if academic.semester not in semesters:
                    semester_grades = academics.filter(semester=academic.semester)
                    semesters[academic.semester] = {
                        'grades': semester_grades,
                        'gpa': self.calculate_gpa(semester_grades)
                    }
            
            context = {
                'semesters': semesters,
                'csrf_token': get_token(request),
            }
            
            return render(request, 'Examination/academic_records_partial.html', context)

        except Exception as e:
            return HttpResponse(f'Error: {str(e)}', status=500)

    def put(self, request):
        """Handle PUT requests to update existing examination records"""
        if not request.headers.get('HX-Request'):
            return HttpResponse('Bad Request', status=400)
            
        # Verify CSRF token
        if not request.POST.get('csrfmiddlewaretoken'):
            return HttpResponse('CSRF token missing', status=403)

        try:
            exam_id = request.POST.get('exam_id')
            academic = Examination.objects.get(id=exam_id)
            
            # Update fields if provided
            if request.POST.get('register_number'):
                academic.register_number = request.POST.get('register_number')
            if request.POST.get('course_code'):
                academic.course_code = request.POST.get('course_code')
            if request.POST.get('course_name'):
                academic.course_name = request.POST.get('course_name')
            if request.POST.get('internal_mark'):
                academic.internal_mark = request.POST.get('internal_mark')
            if request.POST.get('grade'):
                academic.grade = request.POST.get('grade')
                grade_points = {
                    'S': 10, 'A': 9, 'B': 8, 'C': 7,
                    'D': 6, 'E': 5, 'RA': 0, 'AB': 0
                }
                academic.grade_point = grade_points.get(academic.grade, 0)
            if request.POST.get('credit_hours'):
                academic.credit_hours = Decimal(request.POST.get('credit_hours'))
                academic.credit_point = academic.grade_point * academic.credit_hours
            if request.POST.get('exam_held_on'):
                academic.exam_held_on = request.POST.get('exam_held_on')
            if request.POST.get('regulations'):
                academic.regulations = request.POST.get('regulations')
            
            academic.save()
            
            return self.get(request)
            
        except Examination.DoesNotExist:
            return HttpResponse('Record not found', status=404)
        except Exception as e:
            return HttpResponse(f'Error: {str(e)}', status=500)
        
from django.db.models import F
from itertools import groupby
from operator import attrgetter
from django.utils import timezone

@method_decorator(csrf_exempt, name='dispatch')
class MarksheetDetails(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    session_manager = SessionManager()

    def get(self, request):
        session_id = request.COOKIES.get('session_id')
        
        if not session_id:
            return redirect('student-login')
        
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
            
            user = get_user_model().objects.get(id=session.user_id)
            student_data = Student.objects.filter(roll_number=user.username).first()
            
            if student_data:
                # Get all marksheets and sort them by semester
                marksheets = SemesterMarksheet.objects.filter(
                    roll_number=student_data.roll_number
                ).order_by('semester', '-created_at')
                
                # Group marksheets by semester
                semester_marksheets = {}
                for semester, group in groupby(marksheets, key=attrgetter('semester')):
                    semester_marksheets[semester] = list(group)
                
                context = {
                    'user_type': 'student',
                    'roll_number': student_data.roll_number,
                    'student_type': student_data.student_type,
                    'email': student_data.email,
                    'name': student_data.name if hasattr(student_data, 'name') else None,
                    'semester_marksheets': semester_marksheets
                }
                
                if request.headers.get('HX-Request'):
                    return render(request, 'Examination/semester_marksheet/marksheet_list.html', context)
                return render(request, 'Examination/semester_marksheet/marksheet.html', context)
                
            return HttpResponse('Profile not found', status=404)
            
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            response = redirect('student-login')
            response.delete_cookie('session_id')
            return response

    def post(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return HttpResponse('Unauthorized', status=401)

        try:
            session = self.session_manager.get_session(session_id)
            user = get_user_model().objects.get(id=session.user_id)
            student = Student.objects.filter(roll_number=user.username).first()

            if not student:
                return HttpResponse('Student not found', status=404)

            register_number = request.POST.get('register_number')
            semester = request.POST.get('semester')
            marksheet_file = request.FILES.get('marksheet')

            if not all([register_number, semester, marksheet_file]):
                return HttpResponse('Missing required fields', status=400)

            try:
                register_number = int(register_number)
            except ValueError:
                return HttpResponse('Invalid register number', status=400)

            # Create new marksheet
            marksheet = SemesterMarksheet.objects.create(
                roll_number=student.roll_number,
                register_number=register_number,
                semester=semester,
                marksheet=marksheet_file,
                created_at=timezone.now()
            )

            if request.headers.get('HX-Request'):
                context = {
                    'semester': semester,
                    'marksheets': [marksheet]
                }
                return render(request, 'Examination/semester_marksheet/marksheet_list.html', context)
            return HttpResponse('Marksheet uploaded successfully')

        except Exception as e:
            return HttpResponse(str(e), status=500)

    def delete(self, request, marksheet_id):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return HttpResponse('Unauthorized', status=401)

        try:
            marksheet = SemesterMarksheet.objects.get(id=marksheet_id)
            marksheet.delete()
            return HttpResponse('')
        except SemesterMarksheet.DoesNotExist:
            return HttpResponse('Marksheet not found', status=404)
        


@method_decorator(csrf_exempt, name='dispatch')
class DiplomaMarksheetDetails(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    session_manager = SessionManager()

    def get(self, request):
        session_id = request.COOKIES.get('session_id')
        
        if not session_id:
            return redirect('student-login')
        
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
            
            user = get_user_model().objects.get(id=session.user_id)
            student_data = Student.objects.filter(roll_number=user.username).first()
            
            if student_data:
                # Get all marksheets and sort them by semester
                marksheets = DiplomaMarksheet.objects.filter(
                    roll_number=student_data.roll_number
                ).order_by('semester', '-created_at')
                
                # Group marksheets by semester
                semester_marksheets = {}
                for semester, group in groupby(marksheets, key=attrgetter('semester')):
                    semester_marksheets[semester] = list(group)
                
                context = {
                    'user_type': 'student',
                    'roll_number': student_data.roll_number,
                    'student_type': student_data.student_type,
                    'email': student_data.email,
                    'name': student_data.name if hasattr(student_data, 'name') else None,
                    'semester_marksheets': semester_marksheets
                }
                
                if request.headers.get('HX-Request'):
                    return render(request, 'diploma/dmarksheet_list.html', context)
                return render(request, 'diploma/dmarksheet.html', context)
                
            return HttpResponse('Profile not found', status=404)
            
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            response = redirect('student-login')
            response.delete_cookie('session_id')
            return response

    def post(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return HttpResponse('Unauthorized', status=401)

        try:
            session = self.session_manager.get_session(session_id)
            user = get_user_model().objects.get(id=session.user_id)
            student = Student.objects.filter(roll_number=user.username).first()

            if not student:
                return HttpResponse('Student not found', status=404)

            register_number = request.POST.get('register_number')
            semester = request.POST.get('semester')
            marksheet_file = request.FILES.get('marksheet')

            if not all([register_number, semester, marksheet_file]):
                return HttpResponse('Missing required fields', status=400)

            try:
                register_number = int(register_number)
            except ValueError:
                return HttpResponse('Invalid register number', status=400)

            # Create new marksheet
            marksheet = DiplomaMarksheet.objects.create(
                roll_number=student.roll_number,
                register_number=register_number,
                semester=semester,
                marksheet=marksheet_file,
                created_at=timezone.now()
            )

            if request.headers.get('HX-Request'):
                context = {
                    'semester': semester,
                    'marksheets': [marksheet]
                }
                return render(request, 'diploma/dmarksheet_list.html', context)
            return HttpResponse('Marksheet uploaded successfully')

        except Exception as e:
            return HttpResponse(str(e), status=500)

    def delete(self, request, marksheet_id):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return HttpResponse('Unauthorized', status=401)

        try:
            marksheet = DiplomaMarksheet.objects.get(id=marksheet_id)
            marksheet.delete()
            return HttpResponse('')
        except SemesterMarksheet.DoesNotExist:
            return HttpResponse('Marksheet not found', status=404)
        