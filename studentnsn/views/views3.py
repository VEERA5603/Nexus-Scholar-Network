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
from ..models import Academics, PersonalInformation
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

# views.py
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.middleware.csrf import get_token

class PersonalDocumentsView(View):
    template_name = 'documents/personal_documents.html'
    
    def get(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return redirect('student-login')
            
        try:
            session = SessionManager().get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
                
            user = get_user_model().objects.get(id=session.user_id)
            student = Student.objects.filter(roll_number=user.username).first()
            
            if not student:
                return HttpResponse('Profile not found', status=404)
            
            # Get the PersonalInformation instance first
            personal_info = PersonalInformation.objects.filter(roll_number=student.roll_number).first()
            if not personal_info:
                # Create PersonalInformation if it doesn't exist
                personal_info = PersonalInformation.objects.create(
                    roll_number=student.roll_number,
                    name=student.name,
                    email=student.email
                )
            
            # Now get or initialize personal documents
            documents = PersonalDocuments.objects.filter(roll_number=personal_info).first()
            csrf_token = get_token(request)
            
            context = {
                'documents': documents,
                'student': student,
                'csrf_token': csrf_token
            }
            
            if request.headers.get('HX-Request'):
                return render(request, 'documents/personal_documents_partial.html', context)
            return render(request, self.template_name, context)
            
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            response = redirect('student-login')
            response.delete_cookie('session_id')
            return response

    def post(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return HttpResponse("Unauthorized", status=401)

        try:
            session = SessionManager().get_session(session_id)
            user = get_user_model().objects.get(id=session.user_id)
            student = Student.objects.get(roll_number=user.username)
            
            # Get or create PersonalInformation
            personal_info = PersonalInformation.objects.filter(roll_number=student.roll_number).first()
            if not personal_info:
                personal_info = PersonalInformation.objects.create(
                    roll_number=student.roll_number,
                    name=student.name,
                    email=student.email
                )
            
            # Get or create PersonalDocuments
            documents, created = PersonalDocuments.objects.get_or_create(roll_number=personal_info)
            
            # Handle file uploads with validation
            for field in PersonalDocuments._meta.fields:
                if isinstance(field, models.ImageField):
                    field_name = field.name
                    if field_name in request.FILES:
                        file = request.FILES[field_name]
                        
                        # Basic file validation
                        if file.size > 5 * 1024 * 1024:  # 5MB limit
                            return HttpResponse(f"File {field_name} is too large. Maximum size is 5MB.", status=400)
                        
                        # Check file type
                        allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
                        if file.content_type not in allowed_types:
                            return HttpResponse(f"Invalid file type for {field_name}. Allowed types are JPEG,PNG,JPG", status=400)
                        
                        setattr(documents, field_name, file)
            
            documents.save()
            
            context = {
                'documents': documents,
                'student': student,
                'message': 'Documents uploaded successfully'
            }
            
            return render(request, 'documents/personal_documents_partial.html', context)
            
        except Exception as e:
            return HttpResponse(f"Error: {str(e)}", status=400)
        
from django.http import HttpResponse, FileResponse
from django.views import View
from django.shortcuts import render
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
import os
from PIL import Image
import requests
from urllib.parse import urljoin

@method_decorator(csrf_exempt, name='dispatch')
class PersonalDDView(View):
    session_manager = SessionManager()

    def get(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return HttpResponse(
                "<div class='bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded'>"
                "Session expired. Please login again.</div>"
            )
        
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()

            user = get_user_model().objects.get(id=session.user_id)
            student_docs = PersonalDocuments.objects.filter(roll_number__roll_number=user.username).first()
            
            if not student_docs:
                return render(request, 'documents/documents_download.html', {'documents': {}})
            
            document_fields = {
                field.name: getattr(student_docs, field.name)
                for field in PersonalDocuments._meta.fields
                if isinstance(field, models.ImageField) and getattr(student_docs, field.name)
            }
            
            return render(request, 'documents/documents_download.html', {'documents': document_fields})
            
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            return HttpResponse(
                "<div class='bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded'>"
                "Invalid session. Please login again.</div>"
            )

    def post(self, request):
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return HttpResponse(
                "<div class='bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded'>"
                "Session expired. Please login again.</div>",
                status=400
            )

        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()
            
            user = get_user_model().objects.get(id=session.user_id)
            selected_docs = request.POST.getlist('selected_documents')
            
            if not selected_docs:
                return HttpResponse(
                    "<div class='bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded'>"
                    "Please select at least one document</div>",
                    status=400
                )
            
            student_docs = PersonalDocuments.objects.get(
                roll_number__roll_number=user.username
            )
            
            # Create PDF
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            
            # Get letter page dimensions
            page_width, page_height = letter
            
            # Set margins (adjust as needed)
            margin = 50  # 50 points margin
            
            for doc_name in selected_docs:
                doc_field = getattr(student_docs, doc_name, None)
                if doc_field and doc_field.name:
                    try:
                        image_path = doc_field.path
                        
                        if not os.path.exists(image_path):
                            continue
                        
                        # Get image dimensions
                        img = Image.open(image_path)
                        img_width, img_height = img.size
                        
                        # Calculate aspect ratio
                        aspect = img_height / float(img_width)
                        
                        # Set width to fill page width with margins
                        width = page_width - (2 * margin)
                        height = width * aspect
                        
                        # If height exceeds page height with margins, adjust based on height
                        if height > (page_height - (2 * margin)):
                            height = page_height - (2 * margin)
                            width = height / aspect
                        
                        # Add document title to a new page
                        p.setFont("Helvetica-Bold", 12)
                        title = doc_name.replace('_', ' ').title()
                        p.drawString(margin, page_height - margin, title)
                        
                        # Add image centered on the page
                        x_position = (page_width - width) / 2
                        y_position = (page_height - height) / 2
                        
                        p.drawImage(
                            image_path,
                            x_position,
                            y_position - 20,  # Shift down slightly to account for title
                            width=width,
                            height=height
                        )
                        
                        # Each document gets its own page
                        p.showPage()
                        
                    except Exception as e:
                        print(f"Error processing {doc_name}: {str(e)}")
                        continue
            
            p.save()
            buffer.seek(0)
            
            response = FileResponse(
                buffer,
                content_type='application/pdf',
                as_attachment=True,
                filename=f'documents_{user.username}.pdf'
            )
            return response
            
        except Exception as e:
            print(f"Error: {str(e)}")  # Add this for debugging
            return HttpResponse(
                "<div class='bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded'>"
                f"Error generating PDF: {str(e)}</div>",
                status=500
            )