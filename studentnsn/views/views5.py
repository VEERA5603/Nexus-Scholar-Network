# views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from ..models import (
     SSLC, SSLCMarks, HSC, HSCMarks, 
    PersonalInformation
)
from authnsn.models import Student
from authnsn.session_manager import SessionManager
import jwt
import traceback
from ..models import DiplomaMark,DiplomaStudent

class SchoolDetails(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    session_manager = SessionManager()

    def get_session_user(self, request):
        """Helper method to validate session and get user"""
        session_id = request.COOKIES.get('session_id')
        
        if not session_id:
            return None, None
            
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
                
            user = get_user_model().objects.get(id=session.user_id)
            student = Student.objects.filter(roll_number=user.username).first()
            
            return user, student
            
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            return None, None

    def get(self, request):
        user, student = self.get_session_user(request)
        
        if not user or not student:
            response = redirect('student-login')
            response.delete_cookie('session_id')
            return response

        # Fetch existing records for the student
        try:
            sslc_record = SSLC.objects.filter(
                roll_number__roll_number=student.roll_number
            ).first()
            hsc_record = HSC.objects.filter(
                roll_number__roll_number=student.roll_number
            ).first()
            
            sslc_marks = SSLCMarks.objects.filter(
                roll_number=student.roll_number
            ) if sslc_record else []
            
            hsc_marks = HSCMarks.objects.filter(
                roll_number=student.roll_number
            ) if hsc_record else []

            context = {
                'user_type': 'student',
                'roll_number': student.roll_number,
                'student_type': student.student_type,
                'email': student.email,
                'name': student.name if hasattr(student, 'name') else None,
                'sslc_record': sslc_record,
                'hsc_record': hsc_record,
                'sslc_marks': sslc_marks,
                'hsc_marks': hsc_marks
            }
            
            return render(request, 'school_details.html', context)
            
        except Exception as e:
            return HttpResponse(f'Error: {str(e)}', status=500)

    def post(self, request):
        user, student = self.get_session_user(request)
        
        if not user or not student:
            return HttpResponse('Unauthorized', status=401)

        action = request.POST.get('action')
        record_type = request.POST.get('record_type')
        
        try:
            # Get or create PersonalInformation record
            personal_info, _ = PersonalInformation.objects.get_or_create(
                roll_number=student.roll_number
            )

            if action == 'add':
                if record_type == 'sslc':
                    sslc = SSLC.objects.create(
                        roll_number=personal_info,
                        first_name=request.POST.get('first_name'),
                        last_name=request.POST.get('last_name'),
                        school_name=request.POST.get('school_name'),
                        school_address=request.POST.get('school_address'),
                        board=request.POST.get('board'),
                        sslc_register=request.POST.get('sslc_register'),
                        marks_obtained=request.POST.get('marks_obtained'),
                        sslc_percentage=request.POST.get('sslc_percentage'),
                        passed_year=request.POST.get('passed_year'),
                        emis_number=request.POST.get('emis_number')
                    )
                    
                    # Handle subject marks
                    subjects = request.POST.getlist('subject_name[]')
                    marks = request.POST.getlist('subject_mark[]')
                    
                    for subject, mark in zip(subjects, marks):
                        SSLCMarks.objects.create(
                            roll_number=student.roll_number,
                            sslc_register=sslc.sslc_register,
                            subject_name=subject,
                            subject_mark=mark
                        )
                    
                    return HttpResponse("SSLC record added successfully")
                    
                elif record_type == 'hsc':
                    hsc = HSC.objects.create(
                        roll_number=personal_info,
                        first_name=request.POST.get('first_name'),
                        last_name=request.POST.get('last_name'),
                        school_name=request.POST.get('school_name'),
                        school_address=request.POST.get('school_address'),
                        board=request.POST.get('board'),
                        hsc_register=request.POST.get('hsc_register'),
                        marks_obtained=request.POST.get('marks_obtained'),
                        hsc_percentage=request.POST.get('hsc_percentage'),
                        passed_year=request.POST.get('passed_year'),
                        emis_number=request.POST.get('emis_number')
                    )
                    
                    # Handle subject marks
                    subjects = request.POST.getlist('subject_name[]')
                    marks = request.POST.getlist('subject_mark[]')
                    
                    for subject, mark in zip(subjects, marks):
                        HSCMarks.objects.create(
                            roll_number=student.roll_number,
                            hsc_register=hsc.hsc_register,
                            subject_name=subject,
                            subject_mark=mark
                        )
                    
                    return HttpResponse("HSC record added successfully")

            elif action == 'update':
                if record_type == 'sslc':
                    sslc = SSLC.objects.get(roll_number=personal_info)
                    sslc.first_name = request.POST.get('first_name')
                    sslc.last_name = request.POST.get('last_name')
                    sslc.school_name = request.POST.get('school_name')
                    sslc.school_address = request.POST.get('school_address')
                    sslc.board = request.POST.get('board')
                    sslc.marks_obtained = request.POST.get('marks_obtained')
                    sslc.sslc_percentage = request.POST.get('sslc_percentage')
                    sslc.passed_year = request.POST.get('passed_year')
                    sslc.emis_number = request.POST.get('emis_number')
                    sslc.save()
                    
                    # Update marks
                    SSLCMarks.objects.filter(roll_number=student.roll_number).delete()
                    subjects = request.POST.getlist('subject_name[]')
                    marks = request.POST.getlist('subject_mark[]')
                    
                    for subject, mark in zip(subjects, marks):
                        SSLCMarks.objects.create(
                            roll_number=student.roll_number,
                            sslc_register=sslc.sslc_register,
                            subject_name=subject,
                            subject_mark=mark
                        )
                    
                    return HttpResponse("SSLC record updated successfully")
                
                elif record_type == 'hsc':
                    hsc = HSC.objects.get(roll_number=personal_info)
                    hsc.first_name = request.POST.get('first_name')
                    hsc.last_name = request.POST.get('last_name')
                    hsc.school_name = request.POST.get('school_name')
                    hsc.school_address = request.POST.get('school_address')
                    hsc.board = request.POST.get('board')
                    hsc.marks_obtained = request.POST.get('marks_obtained')
                    hsc.hsc_percentage = request.POST.get('hsc_percentage')
                    hsc.passed_year = request.POST.get('passed_year')
                    hsc.emis_number = request.POST.get('emis_number')
                    hsc.save()
                    
                    # Update marks
                    HSCMarks.objects.filter(roll_number=student.roll_number).delete()
                    subjects = request.POST.getlist('subject_name[]')
                    marks = request.POST.getlist('subject_mark[]')
                    
                    for subject, mark in zip(subjects, marks):
                        HSCMarks.objects.create(
                            roll_number=student.roll_number,
                            hsc_register=hsc.hsc_register,
                            subject_name=subject,
                            subject_mark=mark
                        )
                    
                    return HttpResponse("HSC record updated successfully")

            return HttpResponse("Invalid action", status=400)
            
        except Exception as e:
          error_message = f"Error: {str(e)}\n{traceback.format_exc()}"
          return HttpResponse(error_message, status=500)
        


class DiplomaDetails(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    session_manager = SessionManager()

    def get_session_user(self, request):
        """Helper method to validate session and get user"""
        session_id = request.COOKIES.get('session_id')
        
        if not session_id:
            return None, None
            
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
                
            user = get_user_model().objects.get(id=session.user_id)
            student = Student.objects.filter(roll_number=user.username).first()
            
            return user, student
            
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            return None, None

    def get(self, request):
        """Handle GET request to fetch diploma details"""
        user, student = self.get_session_user(request)
        
        if not user or not student:
            response = redirect('student-login')
            response.delete_cookie('session_id')
            return response

        try:
            diploma_record = DiplomaStudent.objects.filter(
                roll_number__roll_number=student.roll_number
            ).first()
            
            diploma_marks = DiplomaMark.objects.filter(
                roll_number=student.roll_number
            ).order_by('semester') if diploma_record else []

            # Group marks by semester for easier display
            marks_by_semester = {}
            for mark in diploma_marks:
                if mark.semester not in marks_by_semester:
                    marks_by_semester[mark.semester] = []
                marks_by_semester[mark.semester].append(mark)

            context = {
                'user_type': 'student',
                'roll_number': student.roll_number,
                'student_type': student.student_type,
                'email': student.email,
                'name': student.name if hasattr(student, 'name') else None,
                'diploma_record': diploma_record,
                'marks_by_semester': marks_by_semester
            }
            
            return render(request, 'diploma.html', context)
            
        except Exception as e:
            error_message = f"Error fetching diploma details: {str(e)}"
            return HttpResponse(error_message, status=500)

    def post(self, request):
        """Handle POST request to add or update diploma details"""
        user, student = self.get_session_user(request)
        
        if not user or not student:
            return HttpResponse('Unauthorized', status=401)

        action = request.POST.get('action')
        
        try:
            personal_info, _ = PersonalInformation.objects.get_or_create(
                roll_number=student.roll_number
            )

            if action == 'add':
                # Validate required fields
                required_fields = [
                    'diploma_register', 'first_name', 'last_name', 
                    'sslc_register', 'course_name', 'college_name',
                    'percentage', 'year_of_joined', 'year_of_passed'
                ]
                
                for field in required_fields:
                    if not request.POST.get(field):
                        return HttpResponse(f"Missing required field: {field}", status=400)

                # Create diploma record
                diploma = DiplomaStudent.objects.create(
                    roll_number=personal_info,
                    diploma_register=request.POST.get('diploma_register'),
                    first_name=request.POST.get('first_name'),
                    last_name=request.POST.get('last_name'),
                    sslc_register=request.POST.get('sslc_register'),
                    hsc_register=request.POST.get('hsc_register'),
                    course_name=request.POST.get('course_name'),
                    college_name=request.POST.get('college_name'),
                    percentage=request.POST.get('percentage'),
                    year_of_joined=request.POST.get('year_of_joined'),
                    year_of_passed=request.POST.get('year_of_passed')
                )
                
                # Handle semester marks
                semesters = request.POST.getlist('semester[]')
                courses = request.POST.getlist('course_name[]')
                marks = request.POST.getlist('course_mark[]')
                
                if len(semesters) != len(courses) or len(courses) != len(marks):
                    return HttpResponse("Mismatched course and mark data", status=400)
                
                for semester, course, mark in zip(semesters, courses, marks):
                    if not all([semester, course, mark]):
                        continue
                        
                    try:
                        mark_value = int(mark)
                        if not (0 <= mark_value <= 100):
                            raise ValueError("Mark must be between 0 and 100")
                            
                        DiplomaMark.objects.create(
                            diploma_register=diploma.diploma_register,
                            roll_number=student.roll_number,
                            semester=semester,
                            course_name=course,
                            course_mark=mark_value
                        )
                    except ValueError as ve:
                        return HttpResponse(f"Invalid mark value: {str(ve)}", status=400)
                
                return HttpResponse("Diploma record added successfully")

            elif action == 'update':
                try:
                    diploma = DiplomaStudent.objects.get(roll_number=personal_info)
                except DiplomaStudent.DoesNotExist:
                    return HttpResponse("Diploma record not found", status=404)

                # Update diploma record
                fields_to_update = [
                    'first_name', 'last_name', 'sslc_register', 'hsc_register',
                    'course_name', 'college_name', 'percentage', 
                    'year_of_joined', 'year_of_passed'
                ]
                
                for field in fields_to_update:
                    if value := request.POST.get(field):
                        setattr(diploma, field, value)
                
                diploma.save()
                
                # Update marks
                DiplomaMark.objects.filter(
                    roll_number=student.roll_number,
                    diploma_register=diploma.diploma_register
                ).delete()
                
                semesters = request.POST.getlist('semester[]')
                courses = request.POST.getlist('course_name[]')
                marks = request.POST.getlist('course_mark[]')
                
                if len(semesters) != len(courses) or len(courses) != len(marks):
                    return HttpResponse("Mismatched course and mark data", status=400)
                
                for semester, course, mark in zip(semesters, courses, marks):
                    if not all([semester, course, mark]):
                        continue
                        
                    try:
                        mark_value = int(mark)
                        if not (0 <= mark_value <= 100):
                            raise ValueError("Mark must be between 0 and 100")
                            
                        DiplomaMark.objects.create(
                            diploma_register=diploma.diploma_register,
                            roll_number=student.roll_number,
                            semester=semester,
                            course_name=course,
                            course_mark=mark_value
                        )
                    except ValueError as ve:
                        return HttpResponse(f"Invalid mark value: {str(ve)}", status=400)
                
                return HttpResponse("Diploma record updated successfully")

            elif action == 'delete':
                try:
                    diploma = DiplomaStudent.objects.get(roll_number=personal_info)
                    DiplomaMark.objects.filter(
                        roll_number=student.roll_number,
                        diploma_register=diploma.diploma_register
                    ).delete()
                    diploma.delete()
                    return HttpResponse("Diploma record deleted successfully")
                except DiplomaStudent.DoesNotExist:
                    return HttpResponse("Diploma record not found", status=404)

            return HttpResponse("Invalid action", status=400)
            
        except Exception as e:
            error_message = f"Error: {str(e)}\n{traceback.format_exc()}"
            return HttpResponse(error_message, status=500)