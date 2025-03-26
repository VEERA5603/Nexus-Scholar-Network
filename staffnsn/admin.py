from django.contrib import admin
from django.contrib import admin
from .models import StudentsAttendance,AttendancePercentage, Faculty, PublicationCategory, Publication, ResearchGuidance, ResearchProject, Award, AcademicEvent
# Register your models here.
admin.site.register(Faculty)
admin.site.register(PublicationCategory)
admin.site.register(Publication)
admin.site.register(AcademicEvent)
admin.site.register(Award)
admin.site.register(ResearchGuidance)
admin.site.register(ResearchProject)