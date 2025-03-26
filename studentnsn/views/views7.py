from django.views import View
from django.utils.decorators import method_decorator
from ..models import BriefDetails, PersonalInformation, Hosteller, BankDetails, Academics, SSLC, HSC, DiplomaStudent, RejoinStudent, Scholarship
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from authnsn.models import Student
from authnsn.session_manager import SessionManager
from django.views.decorators.csrf import csrf_exempt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from datetime import datetime
import jwt
import os
import os
from reportlab.platypus import Image
from django.conf import settings
from urllib.request import urlopen
from PIL import Image as PILImage
from reportlab.lib.utils import ImageReader


class ReportDetails(View):
    authentication_classes = []
    permission_classes = [AllowAny]
    session_manager = SessionManager()

    def get(self, request):
        """Handle GET request to show the PDF generation form"""
        session_id = request.COOKIES.get('session_id')
        
        if not session_id:
            return redirect('student-login')
        
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()

            user = get_user_model().objects.get(id=session.user_id)
            
            # Check if user is a student
            student_data = Student.objects.filter(roll_number=user.username).first()
            if student_data:
                context = {
                    'user_type': 'student',
                    'roll_number': student_data.roll_number,
                    'student_type': student_data.student_type,
                    'email': student_data.email,
                    'name': student_data.name if hasattr(student_data, 'name') else None
                }
                return render(request, 'report.html', context)

            return HttpResponse('Profile not found', status=404)
            
        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            response = redirect('student-login')
            response.delete_cookie('session_id')
            return response

    def generate_personal_info_table(self, user_data):
        """Generate table for personal information"""
        data = [
            ['Field', 'Information'],  # Header row
            ['Roll Number', str(user_data.roll_number)],
            ['Previous Roll Number', str(user_data.previous_roll_number) if user_data.previous_roll_number else 'N/A'],
            ['Type of Student', dict(PersonalInformation.STUDENT_TYPE_CHOICES)[user_data.type_of_student]],
            ['First Name', user_data.first_name],
            ['Last Name', user_data.last_name],
            ['Date of Birth', str(user_data.dob)],
            ['Gender', user_data.gender],
            ['Blood Group', user_data.blood_group],
            ['Religion', user_data.religion],
            ['Community', user_data.community],
            ['Caste', user_data.caste],
            ['Nationality', user_data.nationality],
            ['Student Mobile', str(user_data.student_mobile)],
            ['Email', user_data.email],
            ['Aadhar Number', str(user_data.aadhar_number)],
            ['Father Name', user_data.father_name],
            ['Father Occupation', user_data.father_occupation],
            ['Father Mobile', str(user_data.father_mobile)],
            ['Mother Name', user_data.mother_name],
            ['Mother Occupation', user_data.mother_occupation],
            ['Mother Mobile', str(user_data.mother_mobile)],
            ['Annual Income', str(user_data.annual_income)],
            ['Height', str(user_data.height)],
            ['Weight', str(user_data.weight)],
            ['Differently Abled', 'Yes' if user_data.differentially_abled else 'No'],
            ['Type of Disability', user_data.Type_of_disability if user_data.differentially_abled else 'N/A'],
            ['Special Quota', user_data.get_special_quota_display()],
            ['Permanent Address', str(user_data.permanent_address)],
            ['Communication Address', str(user_data.communication_address)]
        ]
        return Table(data)

    def generate_brief_details_table(self, brief_data):
        """Generate table for brief details"""
        data = [
            ['Field', 'Information'],  # Header row
            ['Roll Number', str(brief_data.roll_number)],
            ['Identification Marks', brief_data.identification_marks],
            ['Extracurricular Activities', brief_data.extracurricular_activities],
            ['Brother Name', brief_data.brother_name],
            ['Brother Mobile', brief_data.brother_mobile],
            ['Sister Names', brief_data.sister_names or 'N/A'],
            ['Sister Mobile', brief_data.sister_mobile],
            ['Friends Names', brief_data.friends_names],
            ['Friends Mobile', brief_data.friends_mobile],
            ['Having Vehicle', 'Yes' if brief_data.having_vehicle else 'No'],
            ['Vehicle Number', brief_data.vehicle_number if brief_data.having_vehicle else 'N/A'],
            ['Health Issues', brief_data.any_health_issues],
            ['Hobbies', brief_data.hobbies]
        ]
        return Table(data)
    
    def generate_bank_details_table(self, bank_data):
        """Generate table for bank details"""
        data = [
            ['Field', 'Information'],  # Header row
            ['Roll Number', str(bank_data.roll_number)],
            ['Account Holder', f"{bank_data.first_name} {bank_data.last_name}"],
            ['Account Number', str(bank_data.account_number)],
            ['Branch', bank_data.branch],
            ['IFSC Code', bank_data.ifsc],
            ['MICR Code', str(bank_data.micr)],
            ['Account Type', bank_data.account_type],
            ['Bank Address', bank_data.address],
            ['PAN Number', bank_data.pan_number]
        ]
        return Table(data)
    
    def generate_academics_details_table(self, aca_data):
        """Generate table for academics details"""
        data = [
            ['Field', 'Information'],  # Header row
            ['Roll Number', str(aca_data.roll_number)],
            ['Course', aca_data.course],
            ['Department', aca_data.department],
            ['Current Year', aca_data.current_year],
            ['Current Semester', aca_data.current_semester],
            ['Year Joining', aca_data.year_joining],
            ['Type of Admission', aca_data.type_of_admission],
            ['Admission Type', aca_data.admission_type],
            ['EMIS Number', aca_data.emis_number],
            ['UMIS Number', aca_data.umis_number],
            ['Class Incharge', aca_data.class_incharge],
            ['Class Room Number', aca_data.class_room_number]
        ]
        return Table(data)
    
    def generate_ds_details_table(self, ds_data):
        """Generate table for diploma student details"""
        data = [
            ['Field', 'Information'],  # Header row
            ['Roll Number', str(ds_data.roll_number)],
            ['Diploma Register', ds_data.diploma_register],
            ['First Name', ds_data.first_name],
            ['Last Name', ds_data.last_name],
            ['SSLC Register', ds_data.sslc_register],
            ['HSC Register', ds_data.hsc_register if ds_data.hsc_register else 'N/A'],
            ['Course Name', ds_data.course_name],
            ['College Name', ds_data.college_name],
            ['Percentage', ds_data.percentage],
            ['Year of Joined', ds_data.year_of_joined],
            ['Year of Passed', ds_data.year_of_passed]
        ]
        return Table(data)
    
    def generate_sslc_details_table(self, sslc_data):
        """Generate table for SSLC details"""
        data = [
            ['Field', 'Information'],  # Header row
            ['Roll Number', str(sslc_data.roll_number)],
            ['SSLC Register', sslc_data.sslc_register],
            ['First Name', sslc_data.first_name],
            ['Last Name', sslc_data.last_name],
            ['School Name', sslc_data.school_name],
            ['School Address', sslc_data.school_address],
            ['Board', sslc_data.board],
            ['Marks Obtained', sslc_data.marks_obtained],
            ['SSLC Percentage', sslc_data.sslc_percentage],
            ['Passed Year', sslc_data.passed_year],
            ['EMIS Number', sslc_data.emis_number]
        ]
        return Table(data)
    
    def generate_hsc_details_table(self, hsc_data):
        """Generate table for HSC details"""
        data = [
            ['Field', 'Information'],  # Header row
            ['Roll Number', str(hsc_data.roll_number)],
            ['HSC Register', hsc_data.hsc_register],
            ['First Name', hsc_data.first_name],
            ['Last Name', hsc_data.last_name],
            ['School Name', hsc_data.school_name],
            ['School Address', hsc_data.school_address],
            ['Board', hsc_data.board],
            ['Marks Obtained', hsc_data.marks_obtained],
            ['HSC Percentage', hsc_data.hsc_percentage],
            ['Passed Year', hsc_data.passed_year],
            ['EMIS Number', hsc_data.emis_number]
        ]
        return Table(data)
    
    def generate_rejoin_details_table(self, r_data):
        """Generate table for rejoin student details"""
        data = [
            ['Field', 'Information'],  # Header row
            ['Roll Number', str(r_data.roll_number)],
            ['New Roll Number', r_data.new_roll_number],
            ['Previous Type of Student', r_data.previous_type_of_student],
            ['Year of Discontinue', r_data.year_of_discontinue],
            ['Year of Rejoin', r_data.year_of_rejoin],
            ['Reason for Discontinue', r_data.reason_for_discontinue]
        ]
        return Table(data)
    
    def generate_host_details_table(self, host_data):
        """Generate table for hostel details"""
        data = [
            ['Field', 'Information'],  # Header row
            ['Roll Number', str(host_data.roll_number)],
            ['First Name', host_data.first_name],
            ['Last Name', host_data.last_name],
            ['Hostel Name', host_data.hostel_name],
            ['Hostel Address', host_data.hostel_address],
            ['From Date', host_data.from_date],
            ['To Date', host_data.to_date],
            ['Room Number', host_data.room_number]
        ]
        return Table(data)
    
    def generate_scholarship_details_table(self, s_data_list):
        """Generate table for scholarship details - handles multiple records"""
        # Create header row
        data = [['Scholarship Type', 'Academic Year', 'Availed']]
    
        # Add data rows for each scholarship record
        for s_data in s_data_list:
           data.append([
               s_data.scholarship_type,
               s_data.academic_year_availed,
               s_data.availed
            ])
    
        return Table(data)
    
    def generate_pdf(self, request, selected_tables, user):
        """Generate PDF with selected tables"""
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            leftMargin=25,
            rightMargin=25,
            topMargin=25,
            bottomMargin=25
        )
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        # Import necessary modules if not already imported
        from reportlab.lib.colors import Color

        # Define Annamalai University colors
        university_gold = Color(1, 0.85, 0, alpha=1)  # Gold #FFD700
        university_navy = Color(0, 0.13, 0.28, alpha=1)  # Navy Blue #002147
        # Custom styles for elegant presentation
        title_style = ParagraphStyle(
            'DocumentTitle',
            parent=styles['Heading1'],
            fontSize=18,
            fontName='Helvetica-Bold',
            alignment=1,  # Center alignment
            spaceAfter=6,
            textColor=university_gold 
        )
        
        subtitle_style = ParagraphStyle(
            'DocumentSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            fontName='Helvetica-Bold',
            alignment=1,  # Center alignment
            spaceAfter=10,
            textColor=colors.darkblue
        )
        
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading3'],
            fontSize=14,
            fontName='Helvetica-Bold',
            spaceAfter=6,
            textColor=colors.darkslateblue,
            borderWidth=0,
            borderPadding=0,
            borderColor=colors.darkblue,
            borderRadius=None
        )
        
        
        # Add university logo from internet
        logo_url = "https://ts2.mm.bing.net/th?id=OIP.STljN84T2Rdft8S2z8vG8wAAAA&pid=15.1"  # Replace with actual URL
        try:
            # Fetch image from URL
            image_data = urlopen(logo_url).read()
            # Create temporary file-like object
            img_stream = BytesIO(image_data)
            # Create reportlab Image directly from the stream
            logo = Image(img_stream)
            # Set a reasonable width while maintaining aspect ratio
            logo.drawWidth = 70
            # Calculate height to maintain aspect ratio
            logo.drawHeight = logo.drawWidth
            # Center the image
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 5))
        except Exception as e:
            # If logo loading fails, continue without the logo
            print(f"Failed to load logo: {str(e)}")
        
        # Add document title and subtitle
        elements.append(Paragraph("ANNAMALAI UNIVERSITY", title_style))
        elements.append(Paragraph("Department of Information Technology", subtitle_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph("STUDENT DETAILS REPORT", title_style))
        
        # Add date and student info
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=2  # Right alignment
        )
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", date_style))
        elements.append(Spacer(1, 20))
        
        # Get student info
        try:
            personal_info = PersonalInformation.objects.get(roll_number=user.username)
            student_name = f"{personal_info.first_name} {personal_info.last_name}"
            student_info = f"Roll Number: {personal_info.roll_number} | Name: {student_name}"
            elements.append(Paragraph(student_info, styles['Normal']))
            elements.append(Spacer(1, 20))
        except PersonalInformation.DoesNotExist:
            elements.append(Paragraph("Student information not available", styles['Normal']))
            elements.append(Spacer(1, 20))
        
        # Define common table style
        table_style = TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGNMENT', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            # Field labels styling
            # Field labels styling
            ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 1), (0, -1), colors.black),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (0, -1), 10),
            ('ALIGNMENT', (0, 1), (0, -1), 'LEFT'),
            ('LEFTPADDING', (0, 1), (0, -1), 8),
            # Field values styling
            ('BACKGROUND', (1, 1), (1, -1), colors.white),
            ('TEXTCOLOR', (1, 1), (1, -1), colors.black),
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
            ('FONTSIZE', (1, 1), (1, -1), 10),
            ('ALIGNMENT', (1, 1), (1, -1), 'LEFT'),
            ('LEFTPADDING', (1, 1), (1, -1), 8),
            # Grid lines
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ])
        
        # Process each selected table
        for table_name in selected_tables:
            try:
                if table_name == 'personal':
                    elements.append(Paragraph("Personal Information", section_style))
                    elements.append(Spacer(1, 6))
                    table = self.generate_personal_info_table(personal_info)
                    
                elif table_name == 'brief':
                    try:
                        brief_details = BriefDetails.objects.get(roll_number=personal_info)
                        elements.append(Paragraph("Brief Details", section_style))
                        elements.append(Spacer(1, 6))
                        table = self.generate_brief_details_table(brief_details)
                    except BriefDetails.DoesNotExist:
                        elements.append(Paragraph("Brief Details not available", styles['Normal']))
                        elements.append(Spacer(1, 10))
                        continue
                    
                elif table_name == 'bank':
                    try:
                        bank_details = BankDetails.objects.get(roll_number=personal_info)
                        elements.append(Paragraph("Bank Details", section_style))
                        elements.append(Spacer(1, 6))
                        table = self.generate_bank_details_table(bank_details)
                    except BankDetails.DoesNotExist:
                        elements.append(Paragraph("Bank Details not available", styles['Normal']))
                        elements.append(Spacer(1, 10))
                        continue
                    
                elif table_name == 'academics':
                    try:
                        aca_details = Academics.objects.get(roll_number=personal_info)
                        elements.append(Paragraph("Academic Information", section_style))
                        elements.append(Spacer(1, 6))
                        table = self.generate_academics_details_table(aca_details)
                    except Academics.DoesNotExist:
                        elements.append(Paragraph("Academic Information not available", styles['Normal']))
                        elements.append(Spacer(1, 10))
                        continue
                    
                elif table_name == 'sslc':
                    try:
                        sslc_details = SSLC.objects.get(roll_number=personal_info)
                        elements.append(Paragraph("SSLC Details", section_style))
                        elements.append(Spacer(1, 6))
                        table = self.generate_sslc_details_table(sslc_details)
                    except SSLC.DoesNotExist:
                        elements.append(Paragraph("SSLC Details not available", styles['Normal']))
                        elements.append(Spacer(1, 10))
                        continue
                    
                elif table_name == 'hsc':
                    try:
                        hsc_details = HSC.objects.get(roll_number=personal_info)
                        elements.append(Paragraph("HSC Details", section_style))
                        elements.append(Spacer(1, 6))
                        table = self.generate_hsc_details_table(hsc_details)
                    except HSC.DoesNotExist:
                        elements.append(Paragraph("HSC Details not available", styles['Normal']))
                        elements.append(Spacer(1, 10))
                        continue
                    
                elif table_name == 'ds':
                    try:
                        ds_details = DiplomaStudent.objects.get(roll_number=personal_info)
                        elements.append(Paragraph("Diploma Student Details", section_style))
                        elements.append(Spacer(1, 6))
                        table = self.generate_ds_details_table(ds_details)
                    except DiplomaStudent.DoesNotExist:
                        elements.append(Paragraph("Diploma Student Details not available", styles['Normal']))
                        elements.append(Spacer(1, 10))
                        continue
                    
                elif table_name == 'rejoin':
                    try:
                        r_details = RejoinStudent.objects.get(roll_number=personal_info)
                        elements.append(Paragraph("Rejoin Student Details", section_style))
                        elements.append(Spacer(1, 6))
                        table = self.generate_rejoin_details_table(r_details)
                    except RejoinStudent.DoesNotExist:
                        elements.append(Paragraph("Rejoin Student Details not available", styles['Normal']))
                        elements.append(Spacer(1, 10))
                        continue
                    
                elif table_name == 'hostellar':
                    try:
                        host_details = Hosteller.objects.get(roll_number=personal_info)
                        elements.append(Paragraph("Hostel Details", section_style))
                        elements.append(Spacer(1, 6))
                        table = self.generate_host_details_table(host_details)
                    except Hosteller.DoesNotExist:
                        elements.append(Paragraph("Hostel Details not available", styles['Normal']))
                        elements.append(Spacer(1, 10))
                        continue
                    
                elif table_name == 'scholarship':
                    try:
                       # Get all scholarship records for this student
                       scholarship_records = Scholarship.objects.filter(roll_number=personal_info)
        
                       if scholarship_records.exists():
                           elements.append(Paragraph("Scholarship Details", section_style))
                           elements.append(Spacer(1, 6))
                           table = self.generate_scholarship_details_table(scholarship_records)
            
                       # Apply table style
                       scholarship_table_style = TableStyle([
                      # Header row styling
                      ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                      ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                      ('ALIGNMENT', (0, 0), (-1, 0), 'CENTER'),
                      ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                      ('FONTSIZE', (0, 0), (-1, 0), 12),
                      ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                      ('TOPPADDING', (0, 0), (-1, 0), 12),
                      # Data rows styling
                      ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                      ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                      ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                      ('FONTSIZE', (0, 1), (-1, -1), 10),
                      ('ALIGNMENT', (0, 1), (-1, -1), 'LEFT'),
                      ('LEFTPADDING', (0, 1), (-1, -1), 8),
                      # Grid lines
                      ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                      ])
            
                       table.setStyle(scholarship_table_style)
            
            # Set column widths for better readability
                       col_widths = [200, 150, 100]
                       table._argW = col_widths
            
                       elements.append(table)
                       elements.append(Spacer(1, 20))
                       """ else:
                           elements.append(Paragraph("Scholarship Details not available", styles['Normal']))
                           elements.append(Spacer(1, 10))"""
                    except Exception as e:
                        elements.append(Paragraph(f"Error processing Scholarship details: {str(e)}", styles['Normal']))
                        elements.append(Spacer(1, 10))
                        continue
                
                # Apply table style and set widths
                table.setStyle(table_style)
                
                # Set column widths for better readability
                table._argW[0] = 150
                table._argW[1] = 300
                
                elements.append(table)
                elements.append(Spacer(1, 20))
                    
            except Exception as e:
                # This is a general exception handler - only for unexpected errors
                error_text = f"Error processing {table_name.title()} details: {str(e)}"
                elements.append(Paragraph(error_text, styles['Normal']))
                elements.append(Spacer(1, 10))
        
        # Add footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1  # Center alignment
        )
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("This document is computer-generated and does not require a signature.", footer_style))
        elements.append(Paragraph(f"Generated by Department of Information Technology - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", footer_style))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return buffer
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        """Handle POST request to generate PDF"""
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            return HttpResponse('Unauthorized', status=401)

        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                raise jwt.InvalidTokenError()

            user = get_user_model().objects.get(id=session.user_id)
            selected_tables = request.POST.getlist('tables[]')
            
            if not selected_tables:
                return HttpResponse('Please select at least one table', status=400)

            # Use the new generate_pdf method
            buffer = self.generate_pdf(request, selected_tables, user)
            
            # Create response
            response = HttpResponse(buffer.read(), content_type='application/pdf')
            filename = f"Student_Details_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = buffer.tell()
            response['HX-Trigger'] = 'pdfGenerated'
            
            return response

        except (jwt.InvalidTokenError, get_user_model().DoesNotExist):
            return HttpResponse('Unauthorized', status=401)
        except PersonalInformation.DoesNotExist:
            return HttpResponse('Student information not found', status=404)
        except Exception as e:
            return HttpResponse(f'Error generating PDF: {str(e)}', status=500)