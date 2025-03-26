from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Sum, F, ExpressionWrapper, FloatField
from django.db import transaction
from datetime import date, datetime
import jwt
from rest_framework.permissions import AllowAny
from ..models import StudentsAttendance, AttendancePercentage
from studentnsn.models import Academics, PersonalInformation
from authnsn.models import Staff
from django.contrib.auth import get_user_model
from authnsn.session_manager import SessionManager

class StaffAttendanceManagement(APIView):
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
            staff = Staff.objects.filter(staff_id=user.username).first()
            if not staff:
                return HttpResponse('Staff profile not found', status=404)
            
            # Get semester filter if provided
            semester = request.GET.get('semester')
            course_code = request.GET.get('course_code')
            
            # Get today's date for default attendance date
            today = date.today()
            
            context = {
                'user_type': 'staff',
                'staff_id': staff.staff_id,
                'name': getattr(staff, 'name', ''),
                'today': today.strftime('%Y-%m-%d'),
                'selected_semester': semester,
                'selected_course': course_code,
            }
            
            # If semester is selected, show students for attendance marking
            if semester and course_code:
                students = Academics.objects.filter(
                    current_semester=semester
                ).select_related('personal_info')
                
                student_data = []
                for academic in students:
                    student_data.append({
                        'roll_number': academic.personal_info.roll_number,
                        'name': academic.personal_info.name,
                        'semester': academic.current_semester,
                    })
                
                context['students'] = student_data
                context['course_code'] = course_code
                
                # Get existing attendance for today if any
                today_attendance = StudentsAttendance.objects.filter(
                    Date_Attended=today,
                    Course_Code=course_code,
                    staff_name=staff.name
                )
                context['existing_attendance'] = {
                    att.roll_number: att.Is_Present 
                    for att in today_attendance
                }
            
            return render(request, 'staff_attendance.html', context)
            
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            response = redirect('staff-login')
            response.delete_cookie('session_id')
            return response

    def post(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
            
            user = get_user_model().objects.get(id=session.user_id)
            staff = Staff.objects.filter(staff_id=user.username).first()
            if not staff:
                return JsonResponse({'error': 'Staff profile not found'}, status=404)
            
            data = request.POST
            action = data.get('action')
            
            if action == 'mark_attendance':
                return self._mark_attendance(data, staff)
            elif action == 'get_attendance':
                return self._get_attendance_report(data)
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)
                
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            return JsonResponse({'error': 'Session expired'}, status=401)

    def _mark_attendance(self, data, staff):
        try:
            with transaction.atomic():
                date_attended = datetime.strptime(data['date'], '%Y-%m-%d').date()
                from_time = datetime.strptime(data['from_time'], '%H:%M').time()
                to_time = datetime.strptime(data['to_time'], '%H:%M').time()
                no_of_hours = int(data['no_of_hours'])
                course_code = data['course_code']
                course_name = data['course_name']
                semester = data['semester']
                
                # Delete existing attendance for this date/course if any
                StudentsAttendance.objects.filter(
                    Date_Attended=date_attended,
                    Course_Code=course_code,
                    staff_name=staff.name
                ).delete()
                
                # Create new attendance records
                attendance_records = []
                for key, value in data.items():
                    if key.startswith('attendance_'):
                        roll_number = key.split('_')[1]
                        is_present = value == 'true'
                        
                        attendance_records.append(StudentsAttendance(
                            roll_number=roll_number,
                            semester=semester,
                            staff_name=staff.name,
                            Course_Code=course_code,
                            Course_Name=course_name,
                            Date_Attended=date_attended,
                            From_Time=from_time,
                            To_Time=to_time,
                            No_of_Hours=no_of_hours,
                            Is_Present=is_present
                        ))
                
                StudentsAttendance.objects.bulk_create(attendance_records)
                
                # Update attendance percentages
                self._update_attendance_percentages(course_code, semester)
                
                return JsonResponse({'success': True})
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def _get_attendance_report(self, data):
        try:
            semester = data.get('semester')
            course_code = data.get('course_code')
            roll_number = data.get('roll_number')
            
            if not semester:
                return JsonResponse({'error': 'Semester is required'}, status=400)
            
            # Get total classes conducted
            total_classes = StudentsAttendance.objects.filter(
                semester=semester,
                Course_Code=course_code
            ).values('Date_Attended').distinct().count()
            
            if roll_number:
                # Get attendance for specific student
                attendance = StudentsAttendance.objects.filter(
                    roll_number=roll_number,
                    semester=semester,
                    Course_Code=course_code
                ).order_by('Date_Attended')
                
                attendance_data = [{
                    'date': att.Date_attended.strftime('%Y-%m-%d'),
                    'present': att.Is_Present,
                    'hours': att.No_of_Hours
                } for att in attendance]
                
                # Get percentage from AttendancePercentage table
                percentage = AttendancePercentage.objects.filter(
                    roll_number=roll_number,
                    Semester=semester,
                    Course_Code=course_code
                ).first()
                
                return JsonResponse({
                    'attendance': attendance_data,
                    'total_classes': total_classes,
                    'percentage': percentage.Attendance_Percentage if percentage else 0
                })
            else:
                # Get summary for all students in semester/course
                students = Academics.objects.filter(
                    current_semester=semester
                ).select_related('personal_info')
                
                report_data = []
                for academic in students:
                    present_hours = StudentsAttendance.objects.filter(
                        roll_number=academic.personal_info.roll_number,
                        semester=semester,
                        Course_Code=course_code,
                        Is_Present=True
                    ).aggregate(total=Sum('No_of_Hours'))['total'] or 0
                    
                    total_hours = StudentsAttendance.objects.filter(
                        roll_number=academic.personal_info.roll_number,
                        semester=semester,
                        Course_Code=course_code
                    ).aggregate(total=Sum('No_of_Hours'))['total'] or 0
                    
                    percentage = (present_hours / total_hours * 100) if total_hours > 0 else 0
                    
                    report_data.append({
                        'roll_number': academic.personal_info.roll_number,
                        'name': academic.personal_info.name,
                        'present_hours': present_hours,
                        'total_hours': total_hours,
                        'percentage': round(percentage, 2)
                    })
                
                return JsonResponse({
                    'report': report_data,
                    'total_classes': total_classes
                })
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def _update_attendance_percentages(self, course_code, semester):
        # Get all students in this semester
        students = Academics.objects.filter(
            current_semester=semester
        ).select_related('personal_info')
        
        # Calculate percentages for each student
        for academic in students:
            roll_number = academic.personal_info.roll_number
            
            # Calculate present and total hours
            result = StudentsAttendance.objects.filter(
                roll_number=roll_number,
                semester=semester,
                Course_Code=course_code
            ).aggregate(
                present_hours=Sum('No_of_Hours', filter=F('Is_Present')==True),
                total_hours=Sum('No_of_Hours')
            )
            
            present_hours = result['present_hours'] or 0
            total_hours = result['total_hours'] or 0
            
            percentage = (present_hours / total_hours * 100) if total_hours > 0 else 0
            
            # Update or create AttendancePercentage record
            AttendancePercentage.objects.update_or_create(
                roll_number=roll_number,
                Semester=semester,
                Course_Code=course_code,
                defaults={'Attendance_Percentage': percentage}
            )