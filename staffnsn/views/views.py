import bcrypt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from authnsn.models import Staff
from ..models import StudentsAttendance,AttendancePercentage
from authnsn.session_manager import SessionManager
import jwt

class StaffDashboard(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    session_manager = SessionManager()

    def get(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return redirect('staff-login')
        
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
            
            user = get_user_model().objects.get(id=session.user_id)
            staff_data = Staff.objects.filter(staff_id=user.username).first()
            if staff_data:
                context = {
                    'user_type': 'staff',
                    'staff_id': staff_data.staff_id,
                    'email': staff_data.email,
                    'name': getattr(staff_data, 'name', None)
                }
                return render(request, 'staff_dashboard.html', context)

            return HttpResponse('Profile not found', status=404)
            
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            response = redirect('staff-login')
            response.delete_cookie('session_id')
            return response

"""# views.py
from django.views import View
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.contrib.auth import get_user_model
import jwt
import re

class AttendanceView(View):
    template_name = 'attendance/attendance_form.html'

    def get_session_user(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return None

        try:
            session = SessionManager().get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
            
            return get_user_model().objects.get(id=session.user_id)
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            return None

    def get(self, request):
        user = self.get_session_user(request)
        if not user:
            response = redirect('student-login')
            response.delete_cookie('session_id')
            return response

        csrf_token = get_token(request)
        context = {
            'csrf_token': csrf_token,
            'semesters': Academics.CurrentSemester.choices,
            'current_user': user
        }

        if request.headers.get('HX-Request'):
            return render(request, 'attendance/attendance_form_partial.html', context)
        return render(request, self.template_name, context)

class StudentListView(View):
    template_name = 'attendance/student_list.html'

    def get(self, request):
        semester = request.GET.get('semester')
        if not semester:
            return HttpResponse("Semester is required", status=400)

        students = Academics.objects.filter(
            current_semester=semester
        ).select_related('roll_number')

        context = {
            'students': students,
        }
        
        return render(request, self.template_name, context)


from datetime import datetime

class SaveAttendanceView(View):
    def post(self, request):
        try:
            # Debug print
            print("Received POST data:", request.POST)
            
            # Get form data with validation
            course_code = request.POST.get('course_code')
            course_name = request.POST.get('course_name')
            staff_name = request.POST.get('staff_name')
            date_attended = request.POST.get('date_attended')
            from_time = request.POST.get('from_time')
            to_time = request.POST.get('to_time')
            no_of_hours = request.POST.get('no_of_hours')
            semester = request.POST.get('semester')
            present_students = request.POST.getlist('present_students[]')

            # Validate required fields
            required_fields = {
                'course_code': course_code,
                'course_name': course_name,
                'staff_name': staff_name,
                'date_attended': date_attended,
                'from_time': from_time,
                'to_time': to_time,
                'no_of_hours': no_of_hours,
                'semester': semester
            }

            missing_fields = [field for field, value in required_fields.items() if not value]
            if missing_fields:
                return JsonResponse({
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }, status=400)

            # Parse date and validate
            try:
                date_attended = datetime.strptime(date_attended, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'error': 'Invalid date format. Use YYYY-MM-DD'
                }, status=400)

            # Get all students for the semester
            students = Academics.objects.filter(
                current_semester=semester
            ).select_related('roll_number')

            if not students.exists():
                return JsonResponse({
                    'error': f'No students found for semester {semester}'
                }, status=400)

            # Create attendance records
            attendance_records = []
            for student in students:
                roll_number_str = str(student.roll_number)  # Ensure it's a string
                roll_number_match = re.search(r'\((\d+)\)', roll_number_str)
                roll_number = roll_number_match.group(1) if roll_number_match else None  
                attendance_records.append(
                    StudentsAttendance(
                        roll_number=roll_number,
                        semester=semester, 
                        staff_name=staff_name,
                        Course_Code=course_code,
                        Course_Name=course_name,
                        Date_Attended=date_attended,
                        From_Time=from_time,
                        To_Time=to_time,
                        No_of_Hours=int(no_of_hours),
                        Is_Present=str(student.roll_number.roll_number) in present_students
                    )
                )

            # Bulk create the records
            StudentsAttendance.objects.bulk_create(attendance_records)
            
            return JsonResponse({
                'message': 'Attendance saved successfully!',
                'count': len(attendance_records)
            })

        except Exception as e:
            print(f"Error saving attendance: {str(e)}")  # Debug print
            return JsonResponse({
                'error': f'Error saving attendance: {str(e)}'
            }, status=400)

"""

# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.core.exceptions import PermissionDenied
from ..models import (
    Faculty, ResearchGuidance, AcademicEvent, ResearchProject,
    Publication, Award, PublicationCategory
)
from authnsn.session_manager import SessionManager
from django.contrib.auth import get_user_model
import jwt

class Visualization(View):
    session_manager = SessionManager()
    
    def get(self, request):
        # Verify the session and get the staff member
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return redirect('staff-login')
        
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
            
            user = get_user_model().objects.get(id=session.user_id)
            staff_id = user.username
            
            # Get faculty data
            faculty = get_object_or_404(Faculty, staff_id=staff_id)
            
            # Prepare context
            context = {
                'user_type': 'staff',
                'staff_id': staff_id,
                'name': faculty.name
            }
            
            return render(request, 'visualization1.html', context)
            
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            response = redirect('staff-login')
            response.delete_cookie('session_id')
            return response

    def post(self, request):
        # Process any form submissions related to visualization settings
        pass

class VisualizationData(View):
    session_manager = SessionManager()
    
    def get(self, request, data_type):
        # Verify the session and get the staff member
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
            
            user = get_user_model().objects.get(id=session.user_id)
            staff_id = user.username
            
            # Get faculty data
            faculty = get_object_or_404(Faculty, staff_id=staff_id)
            
            # Return data based on the requested data_type
            if data_type == 'research_guidance':
                data = self.get_research_guidance_data(faculty)
            elif data_type == 'academic_events':
                data = self.get_academic_events_data(faculty)
            elif data_type == 'publications':
                data = self.get_publications_data(faculty)
            elif data_type == 'research_projects':
                data = self.get_research_projects_data(faculty)
            elif data_type == 'experience':
                data = self.get_experience_data(faculty)
            else:
                return JsonResponse({'error': 'Invalid data type'}, status=400)
            
            return JsonResponse(data)
            
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            return JsonResponse({'error': 'Authentication failed'}, status=401)
    
    def get_research_guidance_data(self, faculty):
        guidance = ResearchGuidance.objects.filter(faculty=faculty)
        labels = []
        awarded_data = []
        guidance_data = []
        
        for g in guidance:
            labels.append(g.get_discipline_display())
            awarded_data.append(g.awarded)
            guidance_data.append(g.guidance)
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Awarded',
                    'data': awarded_data,
                    'backgroundColor': 'rgba(54, 162, 235, 0.5)',
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'borderWidth': 1
                },
                {
                    'label': 'Under Guidance',
                    'data': guidance_data,
                    'backgroundColor': 'rgba(255, 99, 132, 0.5)',
                    'borderColor': 'rgba(255, 99, 132, 1)',
                    'borderWidth': 1
                }
            ]
        }
    
    def get_academic_events_data(self, faculty):
        events = AcademicEvent.objects.filter(faculty=faculty)
        event_types = dict(AcademicEvent.EVENT_TYPE_CHOICES)
        roles = dict(AcademicEvent.ROLE_CHOICES)
        
        attended_data = []
        conducted_data = []
        labels = []
        
        for event_type_key, event_type_name in event_types.items():
            labels.append(event_type_name)
            
            attended_count = events.filter(
                event_type=event_type_key,
                role='ATTENDED'
            ).first()
            
            conducted_count = events.filter(
                event_type=event_type_key,
                role='CONDUCTED'
            ).first()
            
            attended_data.append(attended_count.count if attended_count else 0)
            conducted_data.append(conducted_count.count if conducted_count else 0)
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Attended',
                    'data': attended_data,
                    'backgroundColor': 'rgba(75, 192, 192, 0.5)',
                    'borderColor': 'rgba(75, 192, 192, 1)',
                    'borderWidth': 1
                },
                {
                    'label': 'Conducted',
                    'data': conducted_data,
                    'backgroundColor': 'rgba(153, 102, 255, 0.5)',
                    'borderColor': 'rgba(153, 102, 255, 1)',
                    'borderWidth': 1
                }
            ]
        }
    
    def get_publications_data(self, faculty):
        categories = PublicationCategory.objects.filter(faculty=faculty).first()
        if not categories:
            return {
                'labels': [],
                'datasets': [{
                    'label': 'Publications',
                    'data': [],
                    'backgroundColor': [],
                    'borderColor': []
                }]
            }
        
        labels = [
            'Journal - National', 
            'Journal - International',
            'Conference - National',
            'Conference - International',
            'Books Published',
            'Popular Articles'
        ]
        
        data = [
            categories.journal_national,
            categories.journal_international,
            categories.conference_national,
            categories.conference_international,
            categories.books_published,
            categories.popular_articles
        ]
        
        background_colors = [
            'rgba(255, 99, 132, 0.5)',
            'rgba(54, 162, 235, 0.5)',
            'rgba(255, 206, 86, 0.5)',
            'rgba(75, 192, 192, 0.5)',
            'rgba(153, 102, 255, 0.5)',
            'rgba(255, 159, 64, 0.5)'
        ]
        
        border_colors = [
            'rgba(255, 99, 132, 1)',
            'rgba(54, 162, 235, 1)',
            'rgba(255, 206, 86, 1)',
            'rgba(75, 192, 192, 1)',
            'rgba(153, 102, 255, 1)',
            'rgba(255, 159, 64, 1)'
        ]
        
        return {
            'labels': labels,
            'datasets': [{
                'label': 'Publications',
                'data': data,
                'backgroundColor': background_colors,
                'borderColor': border_colors,
                'borderWidth': 1
            }]
        }
    
    def get_research_projects_data(self, faculty):
        projects = ResearchProject.objects.filter(faculty=faculty)
        
        # Group by status and project type
        completed_major = projects.filter(status='COMPLETED', project_type='MAJOR').count()
        completed_minor = projects.filter(status='COMPLETED', project_type='MINOR').count()
        ongoing_major = projects.filter(status='ONGOING', project_type='MAJOR').count()
        ongoing_minor = projects.filter(status='ONGOING', project_type='MINOR').count()
        
        # Calculate total funding by category
        completed_major_amount = sum(float(p.amount) for p in projects.filter(status='COMPLETED', project_type='MAJOR'))
        completed_minor_amount = sum(float(p.amount) for p in projects.filter(status='COMPLETED', project_type='MINOR'))
        ongoing_major_amount = sum(float(p.amount) for p in projects.filter(status='ONGOING', project_type='MAJOR'))
        ongoing_minor_amount = sum(float(p.amount) for p in projects.filter(status='ONGOING', project_type='MINOR'))
        
        return {
            'counts': {
                'labels': ['Completed Major', 'Completed Minor', 'Ongoing Major', 'Ongoing Minor'],
                'datasets': [{
                    'label': 'Project Counts',
                    'data': [completed_major, completed_minor, ongoing_major, ongoing_minor],
                    'backgroundColor': [
                        'rgba(75, 192, 192, 0.5)',
                        'rgba(54, 162, 235, 0.5)',
                        'rgba(255, 206, 86, 0.5)',
                        'rgba(153, 102, 255, 0.5)'
                    ],
                    'borderColor': [
                        'rgba(75, 192, 192, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(153, 102, 255, 1)'
                    ],
                    'borderWidth': 1
                }]
            },
            'amounts': {
                'labels': ['Completed Major', 'Completed Minor', 'Ongoing Major', 'Ongoing Minor'],
                'datasets': [{
                    'label': 'Funding Amount (₹)',
                    'data': [completed_major_amount, completed_minor_amount, ongoing_major_amount, ongoing_minor_amount],
                    'backgroundColor': [
                        'rgba(75, 192, 192, 0.5)',
                        'rgba(54, 162, 235, 0.5)',
                        'rgba(255, 206, 86, 0.5)',
                        'rgba(153, 102, 255, 0.5)'
                    ],
                    'borderColor': [
                        'rgba(75, 192, 192, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(153, 102, 255, 1)'
                    ],
                    'borderWidth': 1
                }]
            }
        }
    
    def get_experience_data(self, faculty):
        labels = ['Teaching & Research', 'Industry']
        data = [faculty.teaching_research_experience, faculty.industry_experience]
        
        return {
            'labels': labels,
            'datasets': [{
                'label': 'Experience (Years)',
                'data': data,
                'backgroundColor': [
                    'rgba(255, 99, 132, 0.5)',
                    'rgba(54, 162, 235, 0.5)'
                ],
                'borderColor': [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)'
                ],
                'borderWidth': 1
            }]
        }
            
            
            
