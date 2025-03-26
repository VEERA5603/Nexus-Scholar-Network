# views.py
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
import jwt
from ..models import (
    PersonalInformation, BriefDetails, RejoinStudent, Hosteller, 
    BankDetails, Scholarship, Academics, PersonalDocuments,
    Examination, SSLC, HSC, DiplomaStudent, SemesterMarksheet,
    DiplomaMarksheet
)
from authnsn.session_manager import SessionManager

@method_decorator(ensure_csrf_cookie, name='dispatch')
class DocumentDashboardView(View):
    authentication_classes = []
    permission_classes = [AllowAny]
    session_manager = SessionManager()

    def get_document_status(self, personal_info):
        """Check status of all documents and related data for a student"""
        status = {
            'personal_info': {
                'complete': False,
                'fields': {}
            },
            'brief_details': {
                'complete': False,
                'exists': False
            },
            'rejoin_details': {
                'complete': False,
                'exists': False,
                'required': personal_info.type_of_student == 2  # Only required for rejoin students
            },
            'hostel_details': {
                'complete': False,
                'exists': False
            },
            'bank_details': {
                'complete': False,
                'exists': False
            },
            'scholarships': {
                'complete': False,
                'exists': False
            },
            'academics': {
                'complete': False,
                'exists': False
            },
            'personal_documents': {
                'complete': False,
                'exists': False,
                'missing_docs': []
            },
            'examinations': {
                'complete': False,
                'exists': False
            },
            'sslc': {
                'complete': False,
                'exists': False
            },
            'hsc': {
                'complete': False,
                'exists': False,
                'required': personal_info.type_of_student != 2  # Not required for rejoin students
            },
            'diploma': {
                'complete': False,
                'exists': False,
                'required': personal_info.type_of_student == 1  # Only for lateral entry
            },
            'semester_marksheets': {
                'complete': False,
                'exists': False,
                'count': 0
            },
            'diploma_marksheets': {
                'complete': False,
                'exists': False,
                'count': 0,
                'required': personal_info.type_of_student == 1  # Only for lateral entry
            }
        }

        # Check Personal Information completeness
        required_personal_fields = [
            'first_name', 'last_name', 'dob', 'gender', 'blood_group',
            'religion', 'community', 'caste', 'nationality', 'student_mobile',
            'email', 'aadhar_number', 'father_name', 'father_occupation',
            'mother_name', 'mother_occupation', 'father_mobile', 'mother_mobile',
            'annual_income', 'height', 'weight', 'differentially_abled',
            'permanent_address', 'communication_address'
        ]
        
        missing_personal_fields = []
        for field in required_personal_fields:
            value = getattr(personal_info, field, None)
            if not value:
                missing_personal_fields.append(field)
        
        status['personal_info']['complete'] = len(missing_personal_fields) == 0
        status['personal_info']['fields'] = {
            'missing': missing_personal_fields,
            'total': len(required_personal_fields),
            'filled': len(required_personal_fields) - len(missing_personal_fields)
        }

        # Check Brief Details
        try:
            brief_details = BriefDetails.objects.get(roll_number=personal_info)
            status['brief_details']['exists'] = True
            required_brief_fields = [
                'identification_marks', 'extracurricular_activities',
                'brother_name', 'brother_mobile', 'friends_names',
                'friends_mobile', 'any_health_issues', 'hobbies'
            ]
            missing_brief_fields = []
            for field in required_brief_fields:
                value = getattr(brief_details, field, None)
                if not value:
                    missing_brief_fields.append(field)
            
            status['brief_details']['complete'] = len(missing_brief_fields) == 0
        except BriefDetails.DoesNotExist:
            pass

        # Check Rejoin Details if required
        if status['rejoin_details']['required']:
            try:
                rejoin_details = RejoinStudent.objects.get(roll_number=personal_info)
                status['rejoin_details']['exists'] = True
                required_rejoin_fields = [
                    'new_roll_number', 'previous_type_of_student',
                    'year_of_discontinue', 'year_of_rejoin', 'reason_for_discontinue'
                ]
                missing_rejoin_fields = []
                for field in required_rejoin_fields:
                    value = getattr(rejoin_details, field, None)
                    if not value:
                        missing_rejoin_fields.append(field)
                
                status['rejoin_details']['complete'] = len(missing_rejoin_fields) == 0
            except RejoinStudent.DoesNotExist:
                pass

        # Check Hostel Details
        try:
            hostel_details = Hosteller.objects.get(roll_number=personal_info)
            status['hostel_details']['exists'] = True
            required_hostel_fields = [
                'hostel_name', 'hostel_address', 'from_date', 'room_number'
            ]
            missing_hostel_fields = []
            for field in required_hostel_fields:
                value = getattr(hostel_details, field, None)
                if not value:
                    missing_hostel_fields.append(field)
            
            status['hostel_details']['complete'] = len(missing_hostel_fields) == 0
        except Hosteller.DoesNotExist:
            pass

        # Check Bank Details
        try:
            bank_details = BankDetails.objects.get(roll_number=personal_info)
            status['bank_details']['exists'] = True
            required_bank_fields = [
                'account_number', 'branch', 'ifsc', 'account_type', 'address'
            ]
            missing_bank_fields = []
            for field in required_bank_fields:
                value = getattr(bank_details, field, None)
                if not value:
                    missing_bank_fields.append(field)
            
            status['bank_details']['complete'] = len(missing_bank_fields) == 0
        except BankDetails.DoesNotExist:
            pass

        # Check Scholarships
        scholarships = Scholarship.objects.filter(roll_number=personal_info)
        status['scholarships']['exists'] = scholarships.exists()
        status['scholarships']['complete'] = scholarships.exists()  # Not all students need scholarships

        # Check Academics
        try:
            academics = Academics.objects.get(roll_number=personal_info)
            status['academics']['exists'] = True
            required_academic_fields = [
                'course', 'department', 'current_year', 'current_semester',
                'year_joining', 'type_of_admission', 'admission_type',
                'emis_number', 'umis_number', 'class_incharge', 'class_room_number'
            ]
            missing_academic_fields = []
            for field in required_academic_fields:
                value = getattr(academics, field, None)
                if not value:
                    missing_academic_fields.append(field)
            
            status['academics']['complete'] = len(missing_academic_fields) == 0
        except Academics.DoesNotExist:
            pass

        # Check Personal Documents
        try:
            personal_docs = PersonalDocuments.objects.get(roll_number=personal_info)
            status['personal_documents']['exists'] = True
            required_documents = [
                'student_photo', 'university_id', 'sslc_certificate',
                'community_certificate', 'transfer_certificate',
                'twelfth_marksheet', 'tenth_marksheet', 'aadhar',
                'tnea_provisional'
            ]
            
            # Only require HSC certificate if not a rejoin student
            if personal_info.type_of_student != 2:
                required_documents.append('hsc_certificate')
            
            missing_documents = []
            for doc in required_documents:
                doc_file = getattr(personal_docs, doc, None)
                if not doc_file:
                    missing_documents.append(doc)
            
            status['personal_documents']['complete'] = len(missing_documents) == 0
            status['personal_documents']['missing_docs'] = missing_documents
        except PersonalDocuments.DoesNotExist:
            pass

        # Check Examinations
        examinations = Examination.objects.filter(roll_number=personal_info.roll_number)
        status['examinations']['exists'] = examinations.exists()
        status['examinations']['complete'] = examinations.exists()  # At least one exam record exists

        # Check SSLC
        try:
            sslc = SSLC.objects.get(roll_number=personal_info)
            status['sslc']['exists'] = True
            required_sslc_fields = [
                'school_name', 'school_address', 'board', 'sslc_register',
                'marks_obtained', 'sslc_percentage', 'passed_year', 'emis_number'
            ]
            missing_sslc_fields = []
            for field in required_sslc_fields:
                value = getattr(sslc, field, None)
                if not value:
                    missing_sslc_fields.append(field)
            
            status['sslc']['complete'] = len(missing_sslc_fields) == 0
        except SSLC.DoesNotExist:
            pass

        # Check HSC if required
        if status['hsc']['required']:
            try:
                hsc = HSC.objects.get(roll_number=personal_info)
                status['hsc']['exists'] = True
                required_hsc_fields = [
                    'hsc_register', 'school_name', 'school_address', 'board',
                    'marks_obtained', 'hsc_percentage', 'passed_year', 'emis_number'
                ]
                missing_hsc_fields = []
                for field in required_hsc_fields:
                    value = getattr(hsc, field, None)
                    if not value:
                        missing_hsc_fields.append(field)
                
                status['hsc']['complete'] = len(missing_hsc_fields) == 0
            except HSC.DoesNotExist:
                pass

        # Check Diploma if required
        if status['diploma']['required']:
            try:
                diploma = DiplomaStudent.objects.get(roll_number=personal_info)
                status['diploma']['exists'] = True
                required_diploma_fields = [
                    'diploma_register', 'course_name', 'college_name',
                    'percentage', 'year_of_joined', 'year_of_passed'
                ]
                missing_diploma_fields = []
                for field in required_diploma_fields:
                    value = getattr(diploma, field, None)
                    if not value:
                        missing_diploma_fields.append(field)
                
                status['diploma']['complete'] = len(missing_diploma_fields) == 0
            except DiplomaStudent.DoesNotExist:
                pass

        # Check Semester Marksheets
        semester_marks = SemesterMarksheet.objects.filter(roll_number=personal_info.roll_number)
        status['semester_marksheets']['exists'] = semester_marks.exists()
        status['semester_marksheets']['count'] = semester_marks.count()
        
        # For regular students, we expect at least current_semester-1 marksheets
        if personal_info.type_of_student == 0:  # Regular student
            try:
                academics = Academics.objects.get(roll_number=personal_info)
                expected_semesters = int(academics.current_semester) - 1
                status['semester_marksheets']['complete'] = semester_marks.count() >= expected_semesters
            except Academics.DoesNotExist:
                status['semester_marksheets']['complete'] = False

        # Check Diploma Marksheets if required
        if status['diploma_marksheets']['required']:
            diploma_marks = DiplomaMarksheet.objects.filter(roll_number=personal_info.roll_number)
            status['diploma_marksheets']['exists'] = diploma_marks.exists()
            status['diploma_marksheets']['count'] = diploma_marks.count()
            status['diploma_marksheets']['complete'] = diploma_marks.count() >= 6  # Assuming 6 semesters for diploma

        return status

    def get(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return redirect('home')
        
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
            
            user = get_user_model().objects.get(id=session.user_id)
            if session.user_type != 'student':
                return HttpResponse('Unauthorized', status=403)
            
            # Get student's personal information
            personal_info = PersonalInformation.objects.get(roll_number=user.username)
            
            # Get document status
            document_status = self.get_document_status(personal_info)
            
            context = {
                'document_status': document_status,
                'student': personal_info,
                'roll_number': user.username
            }
            
            if request.headers.get('HX-Request'):
                return render(request, 'Student Details/document_dashboard_partial.html', context)
            return render(request, 'Student Details/document_dashboard.html', context)
            
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist, PersonalInformation.DoesNotExist):
            response = redirect('student-login')
            response.delete_cookie('session_id')
            return response