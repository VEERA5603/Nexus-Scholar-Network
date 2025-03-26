from django.contrib import admin
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Image, Spacer, 
    Table, TableStyle, PageBreak, Frame, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from io import BytesIO
import requests
from django.core.files.temp import NamedTemporaryFile
import os
from .models import AcademicYear, DepartmentActivity, ActivityImage

class ActivityImageInline(admin.TabularInline):
    model = ActivityImage
    extra = 1

@admin.register(DepartmentActivity)
class DepartmentActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'academic_year', 'date', 'created_at')
    list_filter = ('academic_year', 'date')
    search_fields = ('title', 'description')
    inlines = [ActivityImageInline]
    actions = ['export_as_pdf']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def export_as_pdf(self, request, queryset):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="annamalai_it_activities_report.pdf"'
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                              rightMargin=36, leftMargin=36,
                              topMargin=72, bottomMargin=36)
        
        # Custom styles
        styles = getSampleStyleSheet()
        
        # Add custom styles
        styles.add(ParagraphStyle(
            name='UniversityTitle',
            fontSize=20,
            leading=24,
            alignment=1,  # Center
            textColor=colors.HexColor('#002147'),
            fontName='Helvetica-Bold',
            spaceAfter=12
        ))
        
        styles.add(ParagraphStyle(
            name='DepartmentTitle',
            fontSize=16,
            leading=20,
            alignment=1,  # Center
            textColor=colors.HexColor('#FFD700'),
            fontName='Helvetica-Bold',
            spaceAfter=24
        ))
        
        styles.add(ParagraphStyle(
            name='ActivityTitle',
            fontSize=14,
            leading=18,
            textColor=colors.HexColor('#002147'),
            fontName='Helvetica-Bold',
            spaceAfter=12,
            backColor=colors.HexColor('#F5F5F5'),
            borderPadding=(6, 6, 6, 6),
            borderColor=colors.HexColor('#DDDDDD'),
            borderWidth=1
        ))
        
        styles.add(ParagraphStyle(
            name='ActivityMeta',
            fontSize=10,
            leading=12,
            textColor=colors.HexColor('#666666'),
            fontName='Helvetica-Oblique',
            spaceAfter=12
        ))
        
        styles.add(ParagraphStyle(
            name='NormalIndent',
            parent=styles['Normal'],
            leftIndent=12,
            spaceAfter=12,
            fontSize=11,
            leading=14
        ))
        
        # Header canvas function
        def header(canvas, doc):
            # Save the canvas state
            canvas.saveState()
            
            # Draw university header background
            canvas.setFillColor(colors.HexColor('#002147'))
            canvas.rect(0, doc.pagesize[1] - 0.8*inch, doc.pagesize[0], 0.8*inch, fill=True, stroke=False)
            
            # University name and department
            canvas.setFont('Helvetica-Bold', 14)
            canvas.setFillColor(colors.white)
            canvas.drawString(2.2*inch, doc.pagesize[1] - 0.5*inch, "Annamalai University")
            
            canvas.setFont('Helvetica', 12)
            canvas.drawString(2.2*inch, doc.pagesize[1] - 0.7*inch, "Department of Information Technology")
            
            # Footer with page number
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(colors.HexColor('#666666'))
            canvas.drawCentredString(doc.pagesize[0]/2, 15, f"Page {doc.page} - Department Activities Report")
            
            # Restore the canvas state
            canvas.restoreState()
        
        elements = []
        
        # Add cover page content
        cover_elements = [
            Spacer(1, 2*inch),
            Paragraph("Department Activities Report", styles['Title']),
            Spacer(1, 0.5*inch),
            Paragraph("Annamalai University", styles['UniversityTitle']),
            Paragraph("Department of Information Technology", styles['DepartmentTitle']),
            Spacer(1, 1.5*inch)
        ]
        
        # Add summary table
        data = [
            ['<b>Report Period</b>', f"{min([a.academic_year for a in queryset])} to {max([a.academic_year for a in queryset])}"],
            ['<b>Total Activities</b>', str(len(queryset))],
            ['<b>Generated On</b>', queryset[0].created_at.strftime("%B %d, %Y")],
            ['<b>Generated By</b>', str(request.user)],
        ]
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#002147')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('ALIGN', (0,0), (0,-1), 'RIGHT'),
            ('ALIGN', (1,0), (1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F9F9F9')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ]))
        
        cover_elements.extend([table, Spacer(1, 0.5*inch)])
        cover_elements.append(Paragraph("<i>Official Document - Department of Information Technology</i>", 
                                      ParagraphStyle(name='Footer', fontSize=9, alignment=1, textColor=colors.grey)))
        
        elements.extend(cover_elements)
        elements.append(PageBreak())
        
        # Add activities content
        for activity in queryset:
            activity_group = []
            
            # Activity header with background
            activity_group.append(Paragraph(activity.title, styles['ActivityTitle']))
            
            # Metadata
            meta_data = [
                f"<b>Academic Year:</b> {activity.academic_year}",
                f"<b>Date:</b> {activity.date.strftime('%B %d, %Y')}",
                f"<b>Created:</b> {activity.created_at.strftime('%B %d, %Y')}"
            ]
            activity_group.append(Paragraph(" | ".join(meta_data), styles['ActivityMeta']))
            
            # Description
            activity_group.append(Paragraph("<b>Description:</b>", styles['Heading2']))
            activity_group.append(Paragraph(activity.description, styles['NormalIndent']))
            
            # Images
            images = activity.images.all()
            if images.exists():
                activity_group.append(Paragraph("<b>Related Images:</b>", styles['Heading2']))
                for img in images:
                    try:
                        img_path = img.image.path
                        # Maintain aspect ratio
                        img_width = 5*inch
                        img_height = min(4*inch, img_width * (img.image.height / img.image.width))
                        activity_image = Image(img_path, width=img_width, height=img_height)
                        activity_group.append(activity_image)
                        if img.caption:
                            activity_group.append(Paragraph(f"<i>Caption:</i> {img.caption}", 
                                                          ParagraphStyle(name='Caption', fontSize=9, textColor=colors.grey)))
                        activity_group.append(Spacer(1, 12))
                    except Exception as e:
                        print(f"Error loading activity image: {e}")
                        continue
            
            # Keep each activity together, add page break if needed
            elements.append(KeepTogether(activity_group))
            if activity != queryset.last():
                elements.append(PageBreak())
        
        # Build the document
        doc.build(elements, onFirstPage=header, onLaterPages=header)
        pdf = buffer.getvalue()
        buffer.close()
            
        response.write(pdf)
        return response
    
    export_as_pdf.short_description = "Export as Professional PDF Report"

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('year', 'is_current')
    actions = ['set_as_current']
    
    def set_as_current(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one academic year to set as current.", level='error')
            return
        
        # Set all years to not current first
        AcademicYear.objects.all().update(is_current=False)
        
        # Set selected year as current
        selected_year = queryset.first()
        selected_year.is_current = True
        selected_year.save()
        
        self.message_user(request, f"Successfully set {selected_year} as the current academic year.")
    
    set_as_current.short_description = "Set selected year as current academic year"


