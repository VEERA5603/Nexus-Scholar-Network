from django.contrib import admin
from .models import Student, Staff,StaffPassword,StudentPassword
from django.contrib import admin
from .models import LoginAttempt

@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'role', 'attempts', 'locked', 'locked_until')
    list_filter = ('role', 'locked')
    actions = ['unlock_accounts']
    
    def unlock_accounts(self, request, queryset):
        for attempt in queryset:
            attempt.attempts = 0
            attempt.locked = False
            attempt.locked_until = None
            attempt.save()
        self.message_user(request, f"{queryset.count()} accounts unlocked successfully.")
    unlock_accounts.short_description = "Unlock selected accounts"
    
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('roll_number', 'get_full_name', 'student_type', 'email', 'is_registered', 'age')
    search_fields = ('roll_number', 'email', 'mobile_number')
    list_filter = ('student_type', 'is_registered', 'date_of_birth')  # Filtering by student type and registration status
    ordering = ('-date_of_birth',)  # Orders by date of birth descending by default
    
    def get_full_name(self, obj):
        return f"{obj.roll_number} - {obj.get_student_type_display()}"
    get_full_name.short_description = 'Full Name'

    def age(self, obj):
        from datetime import date
        return (date.today() - obj.date_of_birth).days // 365
    age.short_description = 'Age'

    
@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('staff_id', 'date_of_birth', 'email', 'mobile_number', 'is_registered')
    search_fields = ('staff_id', 'email', 'mobile_number')
    list_filter = ('is_registered',)
    ordering = ('-date_of_birth',)
    
@admin.register(StaffPassword)
class StaffPasswordAdmin(admin.ModelAdmin):
    list_display = ['identifier', 'role', 'created_at', 'updated_at']
    list_filter = ['role', 'created_at']
    search_fields = ['identifier']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('User Information', {
            'fields': ('identifier', 'role', 'password_hash')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return False  # Prevent manual password hash creation
    
@admin.register(StudentPassword)
class StudentPasswordAdmin(admin.ModelAdmin):
    list_display = ['identifier', 'role', 'created_at', 'updated_at']
    list_filter = ['role', 'created_at']
    search_fields = ['identifier']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('User Information', {
            'fields': ('identifier', 'role', 'password_hash')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return False  # Prevent manual password hash creation
    
    # Customizing Admin Titles
admin.site.site_header = "Department of Information Technology"
admin.site.site_title = "Admin Panel"
admin.site.index_title = "Welcome to the Admin Dashboard"


# 2. Update your admin.py file to include the custom announcement interface

from django.contrib import admin
from .models import Announcement, AnnouncementImage

class AnnouncementImageInline(admin.TabularInline):
    model = AnnouncementImage
    extra = 1

class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'created_at', 'is_active')
    list_filter = ('priority', 'is_active', 'created_at')
    search_fields = ('title', 'message')
    inlines = [AnnouncementImageInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'message', 'priority', 'is_active')
        }),
    )

admin.site.register(Announcement, AnnouncementAdmin)


# admin.py
from django.contrib import admin
from .models import Event, EventImage

class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 3

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'created_at')
    inlines = [EventImageInline]

@admin.register(EventImage)
class EventImageAdmin(admin.ModelAdmin):
    list_display = ('event', 'caption')


# admin.py
from django.contrib import admin
from .models import Facultylist

@admin.register(Facultylist)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'designation', 'email')
    search_fields = ('name', 'designation')