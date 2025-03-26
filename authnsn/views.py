import bcrypt
from rest_framework.views import APIView, View
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import SimpleRateThrottle
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from .models import Student, Staff, StaffPassword, StudentPassword, LoginAttempt
from .serializers import LoginSerializer, RegisterSerializer
from datetime import timedelta
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render, redirect
from rest_framework.views import APIView
from django.conf import settings
import jwt
from .session_manager import SessionManager
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from datetime import timedelta  # if you need timedelta

from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
import requests
from datetime import datetime, timezone
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
import requests
from datetime import datetime, timezone
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db import transaction, connection
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db import transaction, connection
from django.contrib.auth import get_user_model
from studentnsn.models import (
    PersonalInformation, SSLC, HSC, Examination, 
    SemesterMarksheet, Hosteller, DiplomaStudent, DiplomaMark,
    DiplomaMarksheet, Academics, PersonalDocuments, BankDetails,
    BriefDetails, Scholarship, RejoinStudent, SSLCMarks, HSCMarks
)

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db import transaction, connection
from django.contrib.auth import get_user_model

def map_student_type(student_type):
    """Map Student model student_type to PersonalInformation type_of_student"""
    mapping = {
        'regular': 0,    # Regular
        'lateral': 1,    # Lateral Entry
        'rejoin': 2     # Rejoin
    }
    return mapping.get(student_type, 0)  # Default to Regular if unknown

@receiver(pre_save, sender=Student)
def update_roll_numbers(sender, instance, **kwargs):
    try:
        # Get the old instance if it exists
        old_instance = Student.objects.get(pk=instance.pk)
        
        # Check if any relevant fields have changed
        roll_number_changed = old_instance.roll_number != instance.roll_number
        prev_roll_changed = old_instance.previous_roll_number != instance.previous_roll_number
        student_type_changed = old_instance.student_type != instance.student_type
        
        # If nothing has changed, do nothing
        if not (roll_number_changed or prev_roll_changed or student_type_changed):
            return
            
        # Start transaction to ensure all updates succeed or none do
        with transaction.atomic():
            # Handle roll_number change
            if roll_number_changed:
                old_roll = old_instance.roll_number
                new_roll = instance.roll_number
                
                # Update User model
                User = get_user_model()
                try:
                    user = User.objects.get(username=old_roll)
                    user.username = new_roll
                    user.save()
                except User.DoesNotExist:
                    pass
                
                # Temporarily disable foreign key checks
                with connection.cursor() as cursor:
                    cursor.execute('SET FOREIGN_KEY_CHECKS=0;')
                
                try:
                    # Update all tables with direct roll_number fields
                    StudentPassword.objects.filter(identifier=old_roll).update(identifier=new_roll)
                    SSLCMarks.objects.filter(roll_number=old_roll).update(roll_number=new_roll)
                    HSCMarks.objects.filter(roll_number=old_roll).update(roll_number=new_roll)
                    Examination.objects.filter(roll_number=old_roll).update(roll_number=new_roll)
                    SemesterMarksheet.objects.filter(roll_number=old_roll).update(roll_number=new_roll)
                    DiplomaMark.objects.filter(roll_number=old_roll).update(roll_number=new_roll)
                    DiplomaMarksheet.objects.filter(roll_number=old_roll).update(roll_number=new_roll)

                    # Update PersonalInformation
                    PersonalInformation.objects.filter(roll_number=old_roll).update(roll_number=new_roll)
                    
                    # Update all related OneToOne fields
                    models_to_update = [
                        Hosteller,
                        Academics,
                        PersonalDocuments,
                        BankDetails,
                        BriefDetails,
                        Scholarship,
                        RejoinStudent,
                        SSLC,
                        HSC,
                        DiplomaStudent
                    ]
                    
                    for model in models_to_update:
                        model.objects.filter(roll_number_id=old_roll).update(roll_number_id=new_roll)
                    
                finally:
                    # Re-enable foreign key checks
                    with connection.cursor() as cursor:
                        cursor.execute('SET FOREIGN_KEY_CHECKS=1;')
            
            # Get PersonalInformation instance for updates
            try:
                personal_info = PersonalInformation.objects.get(roll_number=instance.roll_number)
                
                # Handle previous_roll_number change
                if prev_roll_changed:
                    personal_info.previous_roll_number = instance.previous_roll_number
                
                # Handle student_type change
                if student_type_changed:
                    personal_info.type_of_student = map_student_type(instance.student_type)
                
                # Save if any changes were made
                if prev_roll_changed or student_type_changed:
                    personal_info.save()
                    
            except PersonalInformation.DoesNotExist:
                pass
            
    except Student.DoesNotExist:
        # This is a new instance, no need to update anything
        pass

    except Exception as e:
        # Re-enable foreign key checks in case of any error
        with connection.cursor() as cursor:
            cursor.execute('SET FOREIGN_KEY_CHECKS=1;')
        raise e
    
@ensure_csrf_cookie
def home(request):
    context = {
        'nasa_image': None,
        'nasa_title': None,
        'nasa_explanation': None,
        'image_date': None,
        'error_message': None
    }
    return render(request, 'base.html', context)

def get_nasa_apod(request):
    """HTMX endpoint for NASA APOD"""
    nasa_api_key = 'QQNax5jgRnaRiqzYHEgIIfIWYa5aMtgKKdYEvC7P'
    
    # Don't specify a date to get the latest available image
    nasa_url = f'https://api.nasa.gov/planetary/apod?api_key={nasa_api_key}'
    
    try:
        response = requests.get(nasa_url)
        response.raise_for_status()
        nasa_data = response.json()
        
        context = {
            'nasa_image': nasa_data.get('url'),
            'nasa_title': nasa_data.get('title'),
            'nasa_explanation': nasa_data.get('explanation'),
            'image_date': nasa_data.get('date')
        }
    except requests.RequestException as e:
        context = {
            'error_message': f"Failed to fetch NASA image: {str(e)}"
        }
    except Exception as e:
        context = {
            'error_message': f"An unexpected error occurred: {str(e)}"
        }
    
    return render(request, 'nasa_partial.html', context)
# Constants for cache keys

FAILED_ATTEMPTS_KEY_TEMPLATE = "failed_attempts_{identifier}_{role}"

# Utility function to generate JWT tokens
def generate_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh.set_exp(lifetime=timedelta(days=7))  # Set refresh token expiration to 7 days

    access_token = refresh.access_token
    access_token.set_exp(lifetime=timedelta(minutes=15))  # Set access token expiration to 15 minutes

    return {
        'refresh': str(refresh),
        'access': str(access_token),
    }

# Function to hash password using bcrypt
def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# Function to check if password matches the hashed password
def check_password(hashed_password, password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# Custom Throttling Logic for Login Attempts
from django.utils import timezone
from datetime import timedelta

def increment_failed_attempt(identifier, role):
    attempt, created = LoginAttempt.objects.get_or_create(
        identifier=identifier,
        role=role,
        defaults={'attempts': 1}
    )
    
    if not created:
        attempt.attempts += 1
        if attempt.attempts >= 3:
            attempt.locked = True
            attempt.locked_until = timezone.now() + timedelta(hours=24)
        attempt.save()

def handle_throttling(identifier, role):
    try:
        attempt = LoginAttempt.objects.get(identifier=identifier, role=role)
        
        if attempt.locked:
            if attempt.locked_until and attempt.locked_until > timezone.now():
                return True
            else:
                attempt.locked = False
                attempt.locked_until = None
                attempt.attempts = 0
                attempt.save()
                return False
        return False
        
    except LoginAttempt.DoesNotExist:
        return False
    
# Registration View for Students and Staff
class Register(APIView):
    permission_classes = [AllowAny]
    template_name = 'register.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        if request.headers.get('HX-Request'):
            serializer = RegisterSerializer(data=request.POST)
            if not serializer.is_valid():
                return HttpResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            data = serializer.validated_data
            password = data['password']

            if len(password) < 8:
                return Response({'error': 'Password must be at least 8 characters long'}, 
                                status=status.HTTP_400_BAD_REQUEST)

            try:
                if 'roll_number' in data:
                    response = self.register_student(data)
                elif 'staff_id' in data:
                    response = self.register_staff(data)

                if response.status_code != 201:
                    return Response({'error': response.data.get('error', 'Registration failed')}, 
                                    status=response.status_code)
                    
                return Response({'message': 'Registration successful'}, status=status.HTTP_201_CREATED)
            
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return render(request, self.template_name)
    
    def register_student(self, data):
        try:
            roll_number = data['roll_number']
            #previous_roll_number = data.get('previous_roll_number')
            course = data['course']

            if None:
               """ # Validate previous roll number for rejoin students
                student = Student.objects.filter(
                    previous_roll_number=previous_roll_number,
                    student_type='rejoin'
                ).first()
                if not student:
                    return Response({'error': 'Previous roll number not found or not eligible for rejoining.'},
                                    status=status.HTTP_404_NOT_FOUND)"""
            else:
                # Validate roll number and student type
                student = Student.objects.get(roll_number=roll_number, course=course)

            if student.is_registered:
                return Response({'error': 'Student already registered'}, status=status.HTTP_400_BAD_REQUEST)

            # Hash password and save
            hashed_password = hash_password(data['password'])
            user = get_user_model().objects.create_user(username=roll_number, password=data['password'])
            StudentPassword.objects.create(identifier=roll_number, role='student', password_hash=hashed_password)

            student.is_registered = True
            student.save()

            return Response({'message': 'Student registered successfully'}, status=status.HTTP_201_CREATED)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found or mismatch in student type.'}, status=status.HTTP_404_NOT_FOUND)

    def register_staff(self, data):
        try:
            staff = Staff.objects.get(staff_id=data['staff_id'])
            if staff.is_registered:
                return Response({'error': 'Staff already registered'}, status=status.HTTP_400_BAD_REQUEST)

            # Hash the password
            hashed_password = hash_password(data['password'])

            user = get_user_model().objects.create_user(username=staff.staff_id, password=data['password'])
            StaffPassword.objects.create(identifier=staff.staff_id, role='staff', password_hash=hashed_password)

            staff.is_registered = True
            staff.save()
            return Response({'message': 'Staff registered successfully'}, status=status.HTTP_201_CREATED)
        except Staff.DoesNotExist:
            return Response({'error': 'Staff not found'}, status=status.HTTP_404_NOT_FOUND)



class StudentLogin(APIView):
    permission_classes = [AllowAny]
    session_manager = SessionManager()

    def get(self, request):
        session_id = request.COOKIES.get('session_id')
        if session_id:
            session = self.session_manager.get_session(session_id)
            if session and session.user_type == 'student':
                return redirect('profile')
        return render(request, 'login.html')

    def post(self, request):
        roll_number = request.data.get('roll_number')
        password = request.data.get('password')
        
        # Check for account lock
        if handle_throttling(roll_number, 'student'):
            context = {
                'error_message': 'Account locked due to too many failed attempts. Please try again after 24 hours or contact admin.'
            }
            return render(request, 'login.html', context)
            
        try:
            student = Student.objects.get(roll_number=roll_number)
            user_password = StudentPassword.objects.get(identifier=roll_number)
            
            if check_password(user_password.password_hash, password):
                # Reset failed attempts on successful login
                LoginAttempt.objects.filter(identifier=roll_number, role='student').delete()
                
                user = get_user_model().objects.get(username=roll_number)
                tokens = generate_tokens_for_user(user)
               
                session_id = self.session_manager.create_session(
                    user.id, 'student', tokens
                )
                    
                response = redirect('/student/dash/')
                response.set_cookie(
                    'session_id',
                    session_id,
                    max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                    **self.session_manager.cookie_settings
                )
                return response
            else:
                # Increment failed attempt
                increment_failed_attempt(roll_number, 'student')
                
                context = {
                    'error_message': 'Invalid roll number or password. Please try again.'
                }
                return render(request, 'login.html', context)
                
        except (Student.DoesNotExist, StudentPassword.DoesNotExist):
            increment_failed_attempt(roll_number, 'student')
            context = {
                'error_message': 'Invalid roll number or password. Please try again.'
            }
            return render(request, 'login.html', context)

class StaffLogin(APIView):
    permission_classes = [AllowAny]
    session_manager = SessionManager()

    def get(self, request):
        session_id = request.COOKIES.get('session_id')
        if session_id:
            session = self.session_manager.get_session(session_id)
            if session and session.user_type == 'staff':
                return redirect('profile')
        return render(request, 'staff_login.html')

    def post(self, request):
        staff_id = request.data.get('staff_id')
        password = request.data.get('password')

        if handle_throttling(staff_id, 'staff'):
            return HttpResponse(
                """<div id="error-message" class="error-message">
                    Account locked due to too many failed attempts. Please try again after 24 hours or contact admin.
                </div>""",
                status=429
            )

        try:
            staff = Staff.objects.get(staff_id=staff_id)
            user_password = StaffPassword.objects.get(identifier=staff_id, role='staff')

            if check_password(user_password.password_hash, password):
                # Reset failed attempts on successful login
                LoginAttempt.objects.filter(identifier=staff_id, role='staff').delete()
                
                user = get_user_model().objects.get(username=staff_id)
                tokens = generate_tokens_for_user(user)
                
                session_id = self.session_manager.create_session(
                    user.id, 'staff', tokens
                )

                response = HttpResponse()
                response['HX-Redirect'] = '/staff/dash/'
                response.set_cookie(
                    'session_id',
                    session_id,
                    max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                    **self.session_manager.cookie_settings
                )
                return response
            else:
                increment_failed_attempt(staff_id, 'staff')
                return HttpResponse(
                    """<div id="error-message" class="error-message">
                        Invalid credentials
                    </div>""",
                    status=401
                )
        except (Staff.DoesNotExist, StaffPassword.DoesNotExist):
            increment_failed_attempt(staff_id, 'staff')
            return HttpResponse(
                """<div id="error-message" class="error-message">
                    Invalid credentials
                </div>""",
                status=401
            )

            
class Profile(APIView):
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
            
            if session.user_type == 'staff':
                staff_data = Staff.objects.filter(staff_id=user.username).first()
                if staff_data:
                    context = {
                        'user_type': 'staff',
                        'staff_id': staff_data.staff_id,
                        'email': staff_data.email,
                        'name': staff_data.name if hasattr(staff_data, 'name') else None
                    }
                    return render(request, 'staff_profile.html', context)
            else:
                student_data = Student.objects.filter(roll_number=user.username).first()
                if student_data:
                    context = {
                        'user_type': 'student',
                        'roll_number': student_data.roll_number,
                        'course': student_data.course,
                        'email': student_data.email,
                        'name': student_data.name if hasattr(student_data, 'name') else None
                    }
                    return render(request, 'profile.html', context)

            return HttpResponse('Profile not found', status=404)
            
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            response = redirect('student-login')
            response.delete_cookie('session_id')
            return response

@api_view(['POST'])
@permission_classes([AllowAny])
def logout_user(request):
    session_manager = SessionManager()
    session_id = request.COOKIES.get('session_id')
    
    if session_id:
        session = session_manager.get_session(session_id)
        if session:
            session_manager.invalidate_session(session_id)
    
    response = redirect('home')
    response.delete_cookie('session_id')
    return response

# Token Refresh View
from rest_framework_simplejwt.views import TokenRefreshView

class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [IsAuthenticated]  # Restrict refresh to authenticated users



from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, permission_required
from .models import Announcement, AnnouncementImage

def get_announcements(request):
    """HTMX-compatible view to fetch latest announcements with images"""
    announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')[:5]
    
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'authnsn/partials/announcements_list.html', {
            'announcements': announcements
        })
    
    # Regular request (fallback)
    return render(request, 'authnsn/announcements.html', {
        'announcements': announcements
    })

@login_required
@permission_required('authnsn.add_announcement')
def create_announcement(request):
    """View to create a new announcement with optional images"""
    priorities = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]
    
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        priority = request.POST.get('priority', 'medium')
        
        if not title or not message:
            messages.error(request, 'Title and message are required.')
            return render(request, 'admin/authnsn/announcement/create.html', {
                'priorities': priorities
            })
        
        # Create the announcement
        announcement = Announcement.objects.create(
            title=title,
            message=message,
            priority=priority,
            is_active=True
        )
        
        # Handle image uploads
        images = request.FILES.getlist('images')
        for i, image_file in enumerate(images):
            AnnouncementImage.objects.create(
                announcement=announcement,
                image=image_file,
                order=i
            )
        
        messages.success(request, 'Announcement created successfully.')
        return redirect('admin:authnsn_announcement_changelist')
    
    return render(request, 'admin/authnsn/announcement/create.html', {
        'priorities': priorities
    })

@login_required
@permission_required('authnsn.change_announcement')
def update_announcement(request, pk):
    """View to update an existing announcement with images"""
    try:
        announcement = Announcement.objects.get(pk=pk)
    except Announcement.DoesNotExist:
        messages.error(request, 'Announcement not found.')
        return redirect('admin:authnsn_announcement_changelist')
    
    priorities = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]
    
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        priority = request.POST.get('priority', 'medium')
        is_active = request.POST.get('is_active') == 'on'
        
        if not title or not message:
            messages.error(request, 'Title and message are required.')
            return render(request, 'admin/authnsn/announcement/edit.html', {
                'announcement': announcement,
                'priorities': priorities
            })
        
        # Update the announcement
        announcement.title = title
        announcement.message = message
        announcement.priority = priority
        announcement.is_active = is_active
        announcement.save()
        
        # Handle deleted images
        deleted_images = request.POST.getlist('delete_images')
        if deleted_images:
            AnnouncementImage.objects.filter(id__in=deleted_images).delete()
        
        # Handle new image uploads
        images = request.FILES.getlist('images')
        current_max_order = announcement.images.aggregate(max_order=models.Max('order'))['max_order'] or -1
        
        for i, image_file in enumerate(images):
            AnnouncementImage.objects.create(
                announcement=announcement,
                image=image_file,
                order=current_max_order + i + 1
            )
        
        messages.success(request, 'Announcement updated successfully.')
        return redirect('admin:authnsn_announcement_changelist')
    
    return render(request, 'admin/authnsn/announcement/edit.html', {
        'announcement': announcement,
        'priorities': priorities
    })

@login_required
@permission_required('authnsn.delete_announcement')
def delete_announcement(request, pk):
    """View to delete an announcement"""
    try:
        announcement = Announcement.objects.get(pk=pk)
    except Announcement.DoesNotExist:
        messages.error(request, 'Announcement not found.')
        return redirect('admin:authnsn_announcement_changelist')
    
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, 'Announcement deleted successfully.')
        return redirect('admin:authnsn_announcement_changelist')
    
    return render(request, 'admin/authnsn/announcement/delete.html', {
        'announcement': announcement
    })

@login_required
@require_http_methods(["POST"])
def reorder_announcement_images(request, pk):
    """AJAX endpoint to reorder images for an announcement"""
    try:
        announcement = Announcement.objects.get(pk=pk)
    except Announcement.DoesNotExist:
        return HttpResponse(status=404)
    
    image_ids = request.POST.getlist('image_ids[]')
    
    if not image_ids:
        return HttpResponse(status=400)
    
    # Update the order of images
    for i, image_id in enumerate(image_ids):
        try:
            image = AnnouncementImage.objects.get(id=image_id, announcement=announcement)
            image.order = i
            image.save()
        except AnnouncementImage.DoesNotExist:
            pass
    
    return HttpResponse(status=200)

def view_all_announcements(request):
    """View to display all active announcements"""
    announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')
    
    return render(request, 'authnsn/all_announcements.html', {
        'announcements': announcements
    })
    
    
class UpdatePassword(APIView):
    permission_classes = [AllowAny]
    template_name = 'update_password.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        if request.headers.get('HX-Request'):
            # Step 1: Verify user identity
            if 'verify_identity' in request.POST:
                return self.verify_identity(request)
            # Step 2: Update password
            elif 'update_password' in request.POST:
                return self.update_password(request)
            
        return render(request, self.template_name)
    
    def verify_identity(self, request):
        try:
            data = request.POST
            user_type = data.get('user_type')
            
            if user_type == 'student':
                roll_number = data.get('roll_number')
                course = data.get('course')
                dob = data.get('date_of_birth')
                email = data.get('email')
                mobile = data.get('mobile_number')
                
                student = Student.objects.get(
                    roll_number=roll_number,
                    course=course,
                    date_of_birth=dob,
                    email=email,
                    mobile_number=mobile
                )
                
                if not student.is_registered:
                    return Response({'error': 'Student has not registered yet. Please register first.'}, 
                                    status=status.HTTP_400_BAD_REQUEST)
                
                # Return a form for password update
                html_response = """
                <form id="passwordUpdateForm" 
                      hx-post="/update-password/"
                      hx-swap="outerHTML"
                      class="space-y-4">
                    <input type="hidden" name="update_password" value="true">
                    <input type="hidden" name="user_type" value="student">
                    <input type="hidden" name="identifier" value="{}">
                    
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-700">New Password</label>
                        <input type="password" 
                               name="new_password" 
                               class="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
                               required>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-700">Confirm New Password</label>
                        <input type="password" 
                               name="confirm_password" 
                               class="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
                               required>
                    </div>
                    
                    <button type="submit" 
                            class="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition duration-300">
                        Update Password
                    </button>
                </form>
                """.format(roll_number)
                
                return HttpResponse(html_response)
                
            elif user_type == 'staff':
                staff_id = data.get('staff_id')
                dob = data.get('date_of_birth')
                email = data.get('email')
                mobile = data.get('mobile_number')
                
                staff = Staff.objects.get(
                    staff_id=staff_id,
                    date_of_birth=dob,
                    email=email,
                    mobile_number=mobile
                )
                
                if not staff.is_registered:
                    return Response({'error': 'Staff has not registered yet. Please register first.'}, 
                                    status=status.HTTP_400_BAD_REQUEST)
                
                # Return a form for password update
                html_response = """
                <form id="passwordUpdateForm" 
                      hx-post="/update-password/"
                      hx-swap="outerHTML"
                      class="space-y-4">
                    <input type="hidden" name="update_password" value="true">
                    <input type="hidden" name="user_type" value="staff">
                    <input type="hidden" name="identifier" value="{}">
                    
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-700">New Password</label>
                        <input type="password" 
                               name="new_password" 
                               class="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
                               required>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-700">Confirm New Password</label>
                        <input type="password" 
                               name="confirm_password" 
                               class="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
                               required>
                    </div>
                    
                    <button type="submit" 
                            class="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition duration-300">
                        Update Password
                    </button>
                </form>
                """.format(staff_id)
                
                return HttpResponse(html_response)
                
            return Response({'error': 'Invalid user type'}, status=status.HTTP_400_BAD_REQUEST)
            
        except (Student.DoesNotExist, Staff.DoesNotExist):
            return Response({'error': 'User not found or details do not match our records'}, 
                            status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def update_password(self, request):
        try:
            data = request.POST
            user_type = data.get('user_type')
            identifier = data.get('identifier')
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')
            
            if new_password != confirm_password:
                return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)
                
            if len(new_password) < 8:
                return Response({'error': 'Password must be at least 8 characters long'}, 
                                status=status.HTTP_400_BAD_REQUEST)
            
            # Get the user and update password
            user = get_user_model().objects.get(username=identifier)
            user.set_password(new_password)
            user.save()
            
            # Update the hashed password in the password table
            hashed_password = hash_password(new_password)
            
            if user_type == 'student':
                StudentPassword.objects.filter(identifier=identifier).update(password_hash=hashed_password)
            elif user_type == 'staff':
                StaffPassword.objects.filter(identifier=identifier).update(password_hash=hashed_password)
                
            return Response({'message': 'Password updated successfully'}, status=status.HTTP_200_OK)
            
        except get_user_model().DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# views.py
from django.shortcuts import render, get_object_or_404
from .models import Event, EventImage

def event_list(request):
    events = Event.objects.all().order_by('-date')
    return render(request, 'authnsn/event_list.html', {'events': events})

def event_images(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'authnsn/event_images.html', {'event': event})

# views.py
from django.views.generic import ListView
from .models import Facultylist

class FacultyListView(ListView):
    model = Facultylist
    template_name = 'faculty_list.html'
    context_object_name = 'faculty_members'