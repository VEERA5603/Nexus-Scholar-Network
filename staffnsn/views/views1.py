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
from ..models import Faculty, ResearchGuidance, AcademicEvent, ResearchProject, Publication, Award, PublicationCategory
from rest_framework_simplejwt.authentication import JWTAuthentication
import logging
from authnsn.models import Staff
from authnsn.session_manager import SessionManager



logger = logging.getLogger(__name__)

@method_decorator(csrf_protect, name='dispatch')
class FacultyView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    session_manager = SessionManager()

    def get_staff_from_token(self, request):
        session_id = request.COOKIES.get('session_id')
        
        if not session_id:
            return redirect('student-login')
        
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
            user = get_user_model().objects.get(id=session.user_id)
            return user, Staff.objects.filter(staff_id=user.username).first()
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return None, None

    def get(self, request):
        try:
            user, staff_data = self.get_staff_from_token(request)
            if not user or not staff_data:
                return redirect('home')

            personal_info = Faculty.objects.filter(
                staff_id=staff_data.staff_id
            ).first()
            context = {
                'user_type': 'staff',
                'staff_id': staff_data.staff_id,
               # 'student_type': student_data.student_type,
                'email': staff_data.email,
               # 'name': student_data.name if hasattr(student_data, 'name') else None,
                'personal_info': personal_info,
            }
            return render(request, 'Faculty/faculty_information.html', context)
        except Exception as e:
            logger.error(f"GET request error: {str(e)}")
            return HttpResponse("An error occurred", status=500)

    @transaction.atomic
    def post(self, request):
        try:
            user, staff_data = self.get_staff_from_token(request)
            if not user or not staff_data:
                return HttpResponse('Unauthorized', status=401)

            # Log received data for debugging
            logger.debug(f"Received POST data: {request.POST}")

            
            # Prepare personal information data
            personal_info_data = {
                'staff_id': staff_data.staff_id,
                'name': request.POST.get('name', '').strip(),
                'designation': request.POST.get('designation', '').strip(),
                'department': request.POST.get('department'),
                'qualification': request.POST.get('qualification'),
                'specialization': request.POST.get('specialization', '').strip(),
                'date_of_birth': request.POST.get('date_of_birth', '').strip(),
                'date_of_joining': request.POST.get('date_of_joining', '').strip(),
                'present_address': request.POST.get('present_address', '').strip(),
                'contact_number': request.POST.get('contact_number', '').strip(),
                'email': request.POST.get('email', '').strip(),
                'teaching_research_experience': request.POST.get('teaching_research_experience'),
                'industry_experience': request.POST.get('industry_experience', '').strip(),
               
            }


            # Create or update personal information
            personal_info, created = Faculty.objects.update_or_create(
                staff_id=staff_data.staff_id,
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
        return HttpResponse(status=400)

@method_decorator(csrf_protect, name='dispatch')
class ResearchGuidanceview(View):
    authentication_classes = []
    permission_classes = [AllowAny]
    session_manager = SessionManager()
   
    def get_context(self, user):
        personal_info = Faculty.objects.get(staff_id=user.username)
        # Remove the order_by clause or change to a field that exists
        rg_records = ResearchGuidance.objects.filter(faculty=personal_info)
        return {
            'rg_records': rg_records,
            'staff_id': user.username
        }
   
    def get(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return redirect('staff-login')
       
        try:
            session = SessionManager().get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
           
            user = get_user_model().objects.get(id=session.user_id)
            if session.user_type != 'staff':
                return HttpResponse('Unauthorized', status=403)
           
            # Check if we're editing a specific record
            record_id = request.GET.get('id')
            context = self.get_context(user)
           
            if record_id:
                personal_info = Faculty.objects.get(staff_id=user.username)
                record = ResearchGuidance.objects.filter(id=record_id, faculty=personal_info).first()
                if record:
                    context['s_data'] = record
                    context['record_id'] = record_id
           
            if request.headers.get('HX-Request'):
                return render(request, 'RG/rg_form.html', context)
            return render(request, 'RG/rg_details.html', context)
           
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            response = redirect('staff-login')
            response.delete_cookie('session_id')
            return response
   
    def post(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return HttpResponse('Unauthorized', status=401)
        try:
            session = SessionManager().get_session(session_id)
            user = get_user_model().objects.get(id=session.user_id)
            personal_info = Faculty.objects.get(staff_id=user.username)
           
            # Get record ID for update or leave None for create
            record_id = request.POST.get('record_id')
           
            s_data = {
                'faculty': personal_info,
                'discipline': request.POST.get('discipline'),
                'awarded': request.POST.get('awarded'),
                'guidance': request.POST.get('guidance'),
            }
           
            if record_id:
                # Update existing record
                ResearchGuidance.objects.filter(id=record_id, faculty=personal_info).update(**s_data)
                message = 'Information updated successfully!'
            else:
                # Create new record
                ResearchGuidance.objects.create(**s_data)
                message = 'New record added successfully!'
               
            context = self.get_context(user)
            context['message'] = message
            return render(request, 'RG/rg_form.html', context)
        except (ValidationError, ValueError) as e:
            return HttpResponse(str(e), status=400)
        except Exception as e:
            return HttpResponse('An error occurred', status=500)


@method_decorator(csrf_protect, name='dispatch')
class AcademicEventView(View):
    authentication_classes = []
    permission_classes = [AllowAny]
    session_manager = SessionManager()
   
    def get_context(self, user):
        personal_info = Faculty.objects.get(staff_id=user.username)
        event_records = AcademicEvent.objects.filter(faculty=personal_info)
        return {
            'event_records': event_records,
            'staff_id': user.username
        }
   
    def get(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return redirect('staff-login')
       
        try:
            session = SessionManager().get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
           
            user = get_user_model().objects.get(id=session.user_id)
            if session.user_type != 'staff':
                return HttpResponse('Unauthorized', status=403)
           
            # Check if we're editing a specific record
            record_id = request.GET.get('id')
            context = self.get_context(user)
           
            if record_id:
                personal_info = Faculty.objects.get(staff_id=user.username)
                record = AcademicEvent.objects.filter(id=record_id, faculty=personal_info).first()
                if record:
                    context['s_data'] = record
                    context['record_id'] = record_id
           
            if request.headers.get('HX-Request'):
                return render(request, 'events/event_form.html', context)
            return render(request, 'events/event_details.html', context)
           
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            response = redirect('staff-login')
            response.delete_cookie('session_id')
            return response
   
    def post(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return HttpResponse('Unauthorized', status=401)
        try:
            session = SessionManager().get_session(session_id)
            user = get_user_model().objects.get(id=session.user_id)
            personal_info = Faculty.objects.get(staff_id=user.username)
           
            # Get record ID for update or leave None for create
            record_id = request.POST.get('record_id')
           
            s_data = {
                'faculty': personal_info,
                'event_type': request.POST.get('event_type'),
                'role': request.POST.get('role'),
                'count': request.POST.get('count'),
            }
           
            if record_id:
                # Update existing record
                AcademicEvent.objects.filter(id=record_id, faculty=personal_info).update(**s_data)
                message = 'Information updated successfully!'
            else:
                # Create new record
                AcademicEvent.objects.create(**s_data)
                message = 'New record added successfully!'
               
            context = self.get_context(user)
            context['message'] = message
            return render(request, 'events/event_form.html', context)
        except (ValidationError, ValueError) as e:
            return HttpResponse(str(e), status=400)
        except Exception as e:
            return HttpResponse('An error occurred', status=500)

@method_decorator(csrf_protect, name='dispatch')
class ResearchProjectView(View):
    authentication_classes = []
    permission_classes = [AllowAny]
    session_manager = SessionManager()
   
    def get_context(self, user):
        personal_info = Faculty.objects.get(staff_id=user.username)
        rp_records = ResearchProject.objects.filter(faculty=personal_info)
        return {
            'rp_records': rp_records,
            'staff_id': user.username
        }
   
    def get(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return redirect('staff-login')
       
        try:
            session = SessionManager().get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
           
            user = get_user_model().objects.get(id=session.user_id)
            if session.user_type != 'staff':
                return HttpResponse('Unauthorized', status=403)
           
            # Check if we're editing a specific record
            record_id = request.GET.get('id')
            context = self.get_context(user)
           
            if record_id:
                personal_info = Faculty.objects.get(staff_id=user.username)
                record = ResearchProject.objects.filter(id=record_id, faculty=personal_info).first()
                if record:
                    context['s_data'] = record
                    context['record_id'] = record_id
           
            if request.headers.get('HX-Request'):
                return render(request, 'RP/rp_form.html', context)
            return render(request, 'RP/rp_details.html', context)
           
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            response = redirect('staff-login')
            response.delete_cookie('session_id')
            return response
   
    def post(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return HttpResponse('Unauthorized', status=401)
        try:
            session = SessionManager().get_session(session_id)
            user = get_user_model().objects.get(id=session.user_id)
            personal_info = Faculty.objects.get(staff_id=user.username)
           
            # Get record ID for update or leave None for create
            record_id = request.POST.get('record_id')
           
            s_data = {
                'faculty': personal_info,
                'project_title': request.POST.get('project_title'),
                'project_type': request.POST.get('project_type'),
                'status': request.POST.get('status'),
                'amount': request.POST.get('amount')
            }
           
            if record_id:
                # Update existing record
                ResearchProject.objects.filter(id=record_id, faculty=personal_info).update(**s_data)
                message = 'Information updated successfully!'
            else:
                # Create new record
                ResearchProject.objects.create(**s_data)
                message = 'New record added successfully!'
               
            context = self.get_context(user)
            context['message'] = message
            return render(request, 'RP/rp_form.html', context)
        except (ValidationError, ValueError) as e:
            return HttpResponse(str(e), status=400)
        except Exception as e:
            return HttpResponse('An error occurred', status=500)


from datetime import datetime

@method_decorator(csrf_protect, name='dispatch')
class PublicationView(View):
    authentication_classes = []
    permission_classes = [AllowAny]
    session_manager = SessionManager()
   
    def get_context(self, user):
        personal_info = Faculty.objects.get(staff_id=user.username)
        publication_records = Publication.objects.filter(faculty=personal_info)
        return {
            'publication_records': publication_records,
            'staff_id': user.username
        }
   
    def get(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return redirect('staff-login')
       
        try:
            session = SessionManager().get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
           
            user = get_user_model().objects.get(id=session.user_id)
            if session.user_type != 'staff':
                return HttpResponse('Unauthorized', status=403)
           
            # Check if we're editing a specific record
            record_id = request.GET.get('id')
            context = self.get_context(user)
           
            if record_id:
                personal_info = Faculty.objects.get(staff_id=user.username)
                record = Publication.objects.filter(id=record_id, faculty=personal_info).first()
                if record:
                    context['s_data'] = record
                    context['record_id'] = record_id
           
            if request.headers.get('HX-Request'):
                return render(request, 'publication/publication_form.html', context)
            return render(request, 'publication/publication_details.html', context)
           
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            response = redirect('staff-login')
            response.delete_cookie('session_id')
            return response
   
    def post(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return HttpResponse('Unauthorized', status=401)
        try:
            session = SessionManager().get_session(session_id)
            user = get_user_model().objects.get(id=session.user_id)
            personal_info = Faculty.objects.get(staff_id=user.username)
           
            # Get record ID for update or leave None for create
            record_id = request.POST.get('record_id')
           
            s_data = {
                'faculty': personal_info,
                'publication_type': request.POST.get('publication_type'),
                'authors': request.POST.get('authors'),
                'title': request.POST.get('title'),
                'journal_name': request.POST.get('journal_name'),
                'volume': request.POST.get('volume'),
                'number': request.POST.get('number'),
                'pages': request.POST.get('pages'),
                'year': request.POST.get('year'),
            }
            
            # Handle date field - convert to date object if provided
            date_str = request.POST.get('date')
            if date_str:
                try:
                    s_data['date'] = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    raise ValidationError('Invalid date format. Please use YYYY-MM-DD')
           
            if record_id:
                # Update existing record
                Publication.objects.filter(id=record_id, faculty=personal_info).update(**s_data)
                message = 'Publication information updated successfully!'
            else:
                # Create new record
                Publication.objects.create(**s_data)
                message = 'New publication added successfully!'
               
            context = self.get_context(user)
            context['message'] = message
            return render(request, 'publication/publication_form.html', context)
        except (ValidationError, ValueError) as e:
            return HttpResponse(str(e), status=400)
        except Exception as e:
            return HttpResponse('An error occurred', status=500)



@method_decorator(csrf_protect, name='dispatch')
class AwardView(View):
    authentication_classes = []
    permission_classes = [AllowAny]
    session_manager = SessionManager()
   
    def get_context(self, user):
        personal_info = Faculty.objects.get(staff_id=user.username)
        award_records = Award.objects.filter(faculty=personal_info)
        return {
            'award_records': award_records,
            'staff_id': user.username
        }
   
    def get(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return redirect('staff-login')
       
        try:
            session = SessionManager().get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
           
            user = get_user_model().objects.get(id=session.user_id)
            if session.user_type != 'staff':
                return HttpResponse('Unauthorized', status=403)
           
            # Check if we're editing a specific record
            record_id = request.GET.get('id')
            context = self.get_context(user)
           
            if record_id:
                personal_info = Faculty.objects.get(staff_id=user.username)
                record = Award.objects.filter(id=record_id, faculty=personal_info).first()
                if record:
                    context['s_data'] = record
                    context['record_id'] = record_id
           
            if request.headers.get('HX-Request'):
                return render(request, 'awards/award_form.html', context)
            return render(request, 'awards/award_details.html', context)
           
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            response = redirect('staff-login')
            response.delete_cookie('session_id')
            return response
   
    def post(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return HttpResponse('Unauthorized', status=401)
        try:
            session = SessionManager().get_session(session_id)
            user = get_user_model().objects.get(id=session.user_id)
            personal_info = Faculty.objects.get(staff_id=user.username)
           
            # Get record ID for update or leave None for create
            record_id = request.POST.get('record_id')
           
            s_data = {
                'faculty': personal_info,
                'name': request.POST.get('name'),
                'description': request.POST.get('description'),
            }
           
            if record_id:
                # Update existing record
                Award.objects.filter(id=record_id, faculty=personal_info).update(**s_data)
                message = 'Award information updated successfully!'
            else:
                # Create new record
                Award.objects.create(**s_data)
                message = 'New award added successfully!'
               
            context = self.get_context(user)
            context['message'] = message
            return render(request, 'awards/award_form.html', context)
        except (ValidationError, ValueError) as e:
            return HttpResponse(str(e), status=400)
        except Exception as e:
            return HttpResponse('An error occurred', status=500)



logger = logging.getLogger(__name__)

@method_decorator(csrf_protect, name='dispatch')
class PublicationCategoryView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    session_manager = SessionManager()

    def get_staff_from_token(self, request):
        session_id = request.COOKIES.get('session_id')
        
        if not session_id:
            return redirect('student-login')
        
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
            user = get_user_model().objects.get(id=session.user_id)
            return user, Staff.objects.filter(staff_id=user.username).first()
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return None, None

    def get(self, request):
        try:
            user, staff_data = self.get_staff_from_token(request)
            if not user or not staff_data:
                return redirect('home')

            faculty = Faculty.objects.filter(
                staff_id=staff_data.staff_id
            ).first()
            
            publication_category = PublicationCategory.objects.filter(
                faculty=faculty
            ).first()
            
            context = {
                'user_type': 'staff',
                'staff_id': staff_data.staff_id,
                'email': staff_data.email,
                'faculty': faculty,
                'publication_category': publication_category,
            }
            return render(request, 'Faculty/publication_category.html', context)
        except Exception as e:
            logger.error(f"GET request error: {str(e)}")
            return HttpResponse("An error occurred", status=500)

    @transaction.atomic
    def post(self, request):
        try:
            user, staff_data = self.get_staff_from_token(request)
            if not user or not staff_data:
                return HttpResponse('Unauthorized', status=401)

            # Log received data for debugging
            logger.debug(f"Received POST data: {request.POST}")
            
            faculty = Faculty.objects.filter(staff_id=staff_data.staff_id).first()
            if not faculty:
                return HttpResponse('Faculty profile not found', status=404)
            
            # Prepare publication category data
            publication_data = {
                'faculty': faculty,
                'journal_national': request.POST.get('journal_national', 0),
                'journal_international': request.POST.get('journal_international', 0),
                'conference_national': request.POST.get('conference_national', 0),
                'conference_international': request.POST.get('conference_international', 0),
                'books_published': request.POST.get('books_published', 0),
                'popular_articles': request.POST.get('popular_articles', 0),
            }

            # Create or update publication information
            publication, created = PublicationCategory.objects.update_or_create(
                faculty=faculty,
                defaults=publication_data
            )

            success_message = 'Publication information saved successfully!'
            if request.headers.get('HX-Request'):
                return HttpResponse(
                    f'<div class="alert alert-success">{success_message}</div>',
                    headers={'HX-Trigger': 'publicationInfoSaved'}
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