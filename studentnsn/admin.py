from django.contrib import admin
from django.http import HttpResponse
from import_export.admin import ExportMixin
from import_export import resources
from django.db.models import Q
import csv
from .models import (
    Address, PersonalInformation, Academics, PersonalDocuments, 
    Examination, HSC, HSCMarks, SSLC, SSLCMarks, BriefDetails, 
    Hosteller, BankDetails, RejoinStudent, DiplomaMark, DiplomaStudent, 
    SemesterMarksheet, DiplomaMarksheet, Scholarship
)
from django.contrib import admin
from django.utils.http import urlencode
from django.urls import reverse
from django.http import HttpResponseRedirect

class SemesterListFilter(admin.SimpleListFilter):
    title = 'Semester'
    parameter_name = 'semester'
    
    def lookups(self, request, model_admin):
        # Get all unique semesters from Academics table
        semesters = Academics.objects.values_list(
            'current_semester', flat=True
        ).distinct().order_by('current_semester')
        return [(str(sem), f'Semester {sem}') for sem in semesters]
    
    def queryset(self, request, queryset):
        # The actual filtering happens in the get_queryset method of ExportableAdmin
        return queryset
# Base Resource class for Export functionality
class BaseResource(resources.ModelResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add any common export configuration here

class ExportableAdmin(ExportMixin, admin.ModelAdmin):
    actions = ['export_as_excel', 'export_filtered_as_excel']
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        
        # Check if we need to filter by semester
        if 'semester' in request.GET:
            semester = request.GET.get('semester')
            if semester:
                # For Academics model, filter directly by current_semester
                if hasattr(self.model, 'current_semester'):
                    return queryset.filter(current_semester=semester)
                
                # For other models with roll_number field
                # Get all roll numbers from Academics table with this semester
                academic_rolls = Academics.objects.filter(
                    current_semester=semester
                ).values_list('roll_number', flat=True)
                
                # Check how roll_number is defined in this model
                if hasattr(self.model, 'roll_number'):
                    roll_field = self.model._meta.get_field('roll_number')
                    
                    # Check if it's a ForeignKey
                    if hasattr(roll_field, 'remote_field') and roll_field.remote_field:
                        # It's a foreign key - check if it points directly to the PersonalInformation or another model
                        related_model = roll_field.remote_field.model
                        
                        if hasattr(related_model, 'roll_number') and isinstance(related_model._meta.get_field('roll_number'), models.BigIntegerField):
                            # The related model has a direct roll_number field (e.g., PersonalInformation)
                            queryset = queryset.filter(roll_number__roll_number__in=academic_rolls)
                        else:
                            # Direct foreign key to a model that uses roll_number as PK
                            queryset = queryset.filter(roll_number__in=academic_rolls)
                    else:
                        # It's a direct field (BigIntegerField, CharField, etc.)
                        queryset = queryset.filter(roll_number__in=academic_rolls)
        
        return queryset
    
    def export_as_excel(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={meta.verbose_name_plural}.csv'
        
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            row = []
            for field in field_names:
                value = getattr(obj, field)
                if callable(value):
                    value = value()
                row.append(value)
            writer.writerow(row)
        
        return response
    export_as_excel.short_description = "Export selected records as Excel/CSV"
    
    def export_filtered_as_excel(self, request, queryset):
        """Export all filtered records, not just selected ones"""
        # This will respect any filters applied including our semester filter
        queryset = self.get_queryset(request)
        
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={meta.verbose_name_plural}_filtered.csv'
        
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            row = []
            for field in field_names:
                value = getattr(obj, field)
                if callable(value):
                    value = value()
                row.append(value)
            writer.writerow(row)
        
        return response
    export_filtered_as_excel.short_description = "Export all filtered records as Excel/CSV"
# Resources for each model
class AcademicsResource(BaseResource):
    class Meta:
        model = Academics
        fields = ('roll_number', 'course', 'department', 'current_year', 'current_semester', 'year_joining')

class PersonalInformationResource(BaseResource):
    class Meta:
        model = PersonalInformation
        exclude = ('password',)

class ExaminationResource(BaseResource):
    class Meta:
        model = Examination
        fields = '__all__'

class ScholarshipResource(BaseResource):
    class Meta:
        model = Scholarship
        fields = '__all__'

class HSCResource(BaseResource):
    class Meta:
        model = HSC
        fields = '__all__'

class SSLCResource(BaseResource):
    class Meta:
        model = SSLC
        fields = '__all__'

class HostellerResource(BaseResource):
    class Meta:
        model = Hosteller
        fields = '__all__'

# Admin classes with enhanced functionality
@admin.register(Academics)
class AcademicsAdmin(ExportableAdmin):
    resource_class = AcademicsResource
    list_display = ('roll_number', 'course', 'department', 'current_year', 'current_semester', 'year_joining')
    search_fields = ('roll_number__roll_number', 'course', 'department', 'current_year', 'current_semester')
    list_filter = ('current_year', 'current_semester', 'course', 'department')
    ordering = ('-current_semester',)

@admin.register(PersonalInformation)
class PersonalInformationAdmin(ExportableAdmin):
    resource_class = PersonalInformationResource
    list_display = ('roll_number', 'first_name', 'last_name', 'gender', 'dob', 'type_of_student', 'email')
    search_fields = ('roll_number', 'first_name', 'last_name', 'email', 'aadhar_number')
    list_filter = ('gender', 'type_of_student', 'religion', 'community',SemesterListFilter)

@admin.register(Examination)
class ExaminationAdmin(ExportableAdmin):
    resource_class = ExaminationResource
    list_display = ('roll_number', 'register_number', 'semester', 'course_code', 'course_name', 'grade', 'grade_point')
    search_fields = ('roll_number', 'register_number', 'course_code', 'course_name')
    list_filter = ('semester', 'grade', 'exam_held_on', SemesterListFilter)

@admin.register(HSC)
class HSCAdmin(ExportableAdmin):
    resource_class = HSCResource
    list_display = ('roll_number', 'first_name', 'last_name', 'school_name', 'hsc_percentage', 'passed_year')
    search_fields = ('roll_number__roll_number', 'first_name', 'last_name', 'hsc_register')
    list_filter = ('passed_year', 'board', SemesterListFilter)

@admin.register(HSCMarks)
class HSCMarksAdmin(ExportableAdmin):
    list_display = ('roll_number', 'hsc_register', 'subject_name', 'subject_mark')
    search_fields = ('roll_number', 'hsc_register', 'subject_name')
    list_filter = ('subject_name', SemesterListFilter)

@admin.register(SSLC)
class SSLCAdmin(ExportableAdmin):
    resource_class = SSLCResource
    list_display = ('roll_number', 'first_name', 'last_name', 'school_name', 'sslc_percentage', 'passed_year')
    search_fields = ('roll_number__roll_number', 'first_name', 'last_name', 'sslc_register')
    list_filter = ('passed_year', 'board', SemesterListFilter)

@admin.register(SSLCMarks)
class SSLCMarksAdmin(ExportableAdmin):
    list_display = ('roll_number', 'sslc_register', 'subject_name', 'subject_mark')
    search_fields = ('roll_number', 'sslc_register', 'subject_name')
    list_filter = ('subject_name', SemesterListFilter)

@admin.register(BriefDetails)
class BriefDetailsAdmin(ExportableAdmin):
    list_display = ('roll_number', 'having_vehicle', 'vehicle_number')
    search_fields = ('roll_number__roll_number', 'brother_name', 'friends_names')
    list_filter = ('having_vehicle', SemesterListFilter)

@admin.register(Hosteller)
class HostellerAdmin(ExportableAdmin):
    resource_class = HostellerResource
    list_display = ('roll_number', 'first_name', 'last_name', 'hostel_name', 'room_number', 'from_date', 'to_date')
    search_fields = ('roll_number__roll_number', 'first_name', 'last_name', 'hostel_name', 'room_number')
    list_filter = ('hostel_name', 'from_date', SemesterListFilter)

@admin.register(BankDetails)
class BankDetailsAdmin(ExportableAdmin):
    list_display = ('roll_number', 'first_name', 'last_name', 'account_number', 'bank_name', 'branch', 'account_type')
    search_fields = ('roll_number__roll_number', 'first_name', 'last_name', 'account_number', 'ifsc')
    list_filter = ('account_type', SemesterListFilter)  # Removed 'bank_name' from list_filter

    def bank_name(self, obj):
        # Extract bank name from IFSC or address if possible
        return obj.ifsc.split(':')[0] if ':' in obj.ifsc else "Bank"
    
@admin.register(Scholarship)
class ScholarshipAdmin(ExportableAdmin):
    resource_class = ScholarshipResource
    list_display = ('roll_number', 'scholarship_type', 'academic_year_availed', 'amount', 'availed', 'created_at')
    search_fields = ('roll_number__roll_number', 'scholarship_type')
    list_filter = ('scholarship_type', 'academic_year_availed', 'availed', SemesterListFilter)

@admin.register(RejoinStudent)
class RejoinStudentAdmin(ExportableAdmin):
    list_display = ('roll_number', 'new_roll_number', 'previous_type_of_student', 'year_of_discontinue', 'year_of_rejoin')
    search_fields = ('roll_number__roll_number', 'new_roll_number')
    list_filter = ('previous_type_of_student', 'year_of_discontinue', 'year_of_rejoin', SemesterListFilter)

@admin.register(DiplomaStudent)
class DiplomaStudentAdmin(ExportableAdmin):
    list_display = ('roll_number', 'first_name', 'last_name', 'course_name', 'college_name', 'percentage', 'year_of_passed')
    search_fields = ('roll_number__roll_number', 'first_name', 'last_name', 'diploma_register', 'course_name', 'college_name')
    list_filter = ('course_name', 'year_of_joined', 'year_of_passed', SemesterListFilter)

@admin.register(DiplomaMark)
class DiplomaMarkAdmin(ExportableAdmin):
    list_display = ('roll_number', 'diploma_register', 'semester', 'course_name', 'course_mark')
    search_fields = ('roll_number', 'diploma_register', 'course_name')
    list_filter = ('semester', SemesterListFilter)

@admin.register(SemesterMarksheet)
class SemesterMarksheetAdmin(ExportableAdmin):
    list_display = ('roll_number', 'register_number', 'semester', 'created_at')
    search_fields = ('roll_number', 'register_number')
    list_filter = ('semester', 'created_at', SemesterListFilter)

@admin.register(DiplomaMarksheet)
class DiplomaMarksheetAdmin(ExportableAdmin):
    list_display = ('roll_number', 'register_number', 'semester', 'created_at')
    search_fields = ('roll_number', 'register_number')
    list_filter = ('semester', 'created_at', SemesterListFilter)

@admin.register(PersonalDocuments)
class PersonalDocumentsAdmin(ExportableAdmin):
    list_display = ('roll_number',)
    search_fields = ('roll_number__roll_number', SemesterListFilter)

@admin.register(Address)
class AddressAdmin(ExportableAdmin):
    list_display = ('id', 'door_number', 'street_name', 'district', 'state', 'pincode', 'area_type')
    search_fields = ('door_number', 'street_name', 'district', 'state', 'pincode')
    list_filter = ('area_type', 'state', 'district', SemesterListFilter)
# Admin site customization
admin.site.site_header = "Department of Information Technology"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "Welcome to Admin Panel"
