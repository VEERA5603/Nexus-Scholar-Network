from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from authnsn.models import Student
from django.http import HttpResponse
from django.shortcuts import render, redirect
from rest_framework.views import APIView
from django.conf import settings
import jwt
from django.middleware.csrf import get_token
from authnsn.session_manager import SessionManager
from ..models import Examination
import requests

class Studentdashboard(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    session_manager = SessionManager()

    def get_news(self, query=None):
        api_key = "50df80cb53ae477fbbe9171192c9b5b9"  # Replace with your NewsAPI key
        
        if query and query.strip():  # Only use search if query is not empty
            base_url = "https://newsapi.org/v2/everything"
            params = {
                "apiKey": api_key,
                "q": query,
                "pageSize": 20,
                "language": "en",
                "sortBy": "publishedAt"
            }
        else:  # Default technology news
            base_url = "https://newsapi.org/v2/top-headlines"
            params = {
                "apiKey": api_key,
                "category": "technology",
                "pageSize": 20,
                "language": "en"
            }
            
        try:
            response = requests.get(base_url, params=params)
            data = response.json()
            articles = data.get("articles", [])
            
            # If search returns no results, fallback to technology news
            if not articles and query:
                return self.get_news(None)  # Recursively get default tech news
                
            return articles
            
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []

    def get(self, request):
        session_id = request.COOKIES.get('session_id')
        search_query = request.GET.get('search', '').strip()
        is_htmx_request = request.headers.get('HX-Request')

        # If it's an HTMX request for news search
        if is_htmx_request and 'news-search' in request.GET:
            news_articles = self.get_news(search_query)
            return render(request, 'partials/news_section.html', {
                'news_articles': news_articles,
                'is_tech_news': not bool(search_query)
            })
        
        # Regular page load
        if not session_id:
            return redirect('student-login')
        
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()

            user = get_user_model().objects.get(id=session.user_id)
            
            # Get initial technology news articles
            news_articles = self.get_news()
            
            student_data = Student.objects.filter(roll_number=user.username).first()
            if student_data:
                context = {
                    'user_type': 'student',
                    'roll_number': student_data.roll_number,
                    'course': student_data.course,
                    'email': student_data.email,
                    'name': student_data.name if hasattr(student_data, 'name') else None,
                    'news_articles': news_articles,
                    'is_tech_news': True  # Flag for template to show "Technology News" heading
                }
                return render(request, 'student_dashboard.html', context)

            return HttpResponse('Profile not found', status=404)
            
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            response = redirect('student-login')
            response.delete_cookie('session_id')
            return response

from django.views import View
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.db.models import Avg
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import jwt

class VisualDetails(View):
    authentication_classes = []
    permission_classes = [AllowAny]
    session_manager = SessionManager()

    @method_decorator(ensure_csrf_cookie)
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
            
            if not student_data:
                return HttpResponse('Profile not found', status=404)

            # Get initial chart data
            chart_data = self.get_chart_data(student_data.roll_number)

            context = {
                'user_type': 'student',
                'roll_number': student_data.roll_number,
                'student_type': student_data.student_type,
                'email': student_data.email,
                'name': student_data.name if hasattr(student_data, 'name') else None,
                'initial_data': chart_data,
                'csrf_token': get_token(request)
            }
            return render(request, 'visualization.html', context)
            
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            response = redirect('student-login')
            response.delete_cookie('session_id')
            return response

    def get_chart_data(self, roll_number):
        try:
            all_exams = Examination.objects.filter(roll_number=roll_number).order_by('semester')
            
            if not all_exams:
                return {'error': 'No data found'}

            semesters = []
            gpa_data = []
            cgpa_data = []
            
            # Group exams by semester
            semester_groups = {}
            for exam in all_exams:
                if exam.semester not in semester_groups:
                    semester_groups[exam.semester] = []
                semester_groups[exam.semester].append(exam)

            # Calculate GPA and CGPA for each semester
            for semester in sorted(semester_groups.keys()):
                semester_exams = semester_groups[semester]
                semesters.append(f'Semester {semester}')
                
                # Calculate GPA
                total_points = sum(exam.credit_point for exam in semester_exams)
                total_credits = sum(exam.credit_hours for exam in semester_exams)
                gpa = round(total_points / total_credits, 2) if total_credits > 0 else 0
                gpa_data.append(gpa)
                
                # Calculate CGPA up to this semester
                all_previous_exams = [
                    exam for sem, exams in semester_groups.items()
                    for exam in exams if sem <= semester
                ]
                total_points_cumulative = sum(exam.credit_point for exam in all_previous_exams)
                total_credits_cumulative = sum(exam.credit_hours for exam in all_previous_exams)
                cgpa = round(total_points_cumulative / total_credits_cumulative, 2) if total_credits_cumulative > 0 else 0
                cgpa_data.append(cgpa)

            return {
                'labels': semesters,
                'gpa': gpa_data,
                'cgpa': cgpa_data
            }

        except Exception as e:
            return {'error': str(e)}

    def post(self, request, *args, **kwargs):
        try:
            session_id = request.COOKIES.get('session_id')
            if not session_id:
                return JsonResponse({'error': 'Not authenticated'}, status=401)

            session = self.session_manager.get_session(session_id)
            if not session:
                return JsonResponse({'error': 'Invalid session'}, status=401)

            user = get_user_model().objects.get(id=session.user_id)
            student_data = Student.objects.filter(roll_number=user.username).first()
            
            if not student_data:
                return JsonResponse({'error': 'Student not found'}, status=404)

            chart_data = self.get_chart_data(student_data.roll_number)
            return JsonResponse(chart_data)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)