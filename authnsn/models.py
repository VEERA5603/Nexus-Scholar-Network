from django.db import models
from django.core.validators import RegexValidator

from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

class LoginAttempt(models.Model):
    identifier = models.CharField(max_length=20)  # roll_number or staff_id
    role = models.CharField(max_length=10)  # 'student' or 'staff'
    attempts = models.IntegerField(default=0)
    locked = models.BooleanField(default=False)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_attempt = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('identifier', 'role')
    
    def __str__(self):
        return f"{self.identifier} ({self.role}) - Attempts: {self.attempts}"
class Student(models.Model):
    STUDENT_TYPE_CHOICES = [
        ('regular', 'Regular'),
        ('lateral', 'Lateral'),
        ('rejoin', 'Rejoin')
    ]
    class Course(models.TextChoices):
        BE = 'B.E', 'B.E'
        ME = 'M.E', 'M.E'
        PHD = 'PhD', 'PhD'

    roll_number = models.CharField(max_length=20, unique=True)
    course = models.CharField(max_length=5, choices=Course.choices,default=Course.BE)
    previous_roll_number = models.CharField(max_length=20, blank=True, null=True)
    student_type = models.CharField(max_length=10, choices=STUDENT_TYPE_CHOICES)
    previous_student_type = models.CharField(max_length=10, choices=STUDENT_TYPE_CHOICES, blank=True, null=True)
    date_of_birth = models.DateField()
    email = models.EmailField(unique=True)
    mobile_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )
    rejoin_date = models.DateField(blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    is_registered = models.BooleanField(default=False)

    def clean(self):
        # Check if student type is 'rejoin', then validate the required fields
        if self.student_type == 'rejoin':
            if not self.previous_roll_number:
                raise ValidationError('Previous roll number is required for rejoin students.')
            if not self.previous_student_type:
                raise ValidationError('Previous student type is required for rejoin students.')
            if not self.rejoin_date:
                raise ValidationError('Rejoin date is required for rejoin students.')
            if not self.reason:
                raise ValidationError('Reason is required for rejoin students.')
        else:
            # Ensure the rejoin-related fields are empty for non-rejoin students
            if self.previous_roll_number or self.previous_student_type or self.rejoin_date or self.reason:
                raise ValidationError('Previous student details and rejoin date are not required for non-rejoin students.')

    def _str_(self):
        return f"{self.roll_number} - {self.get_student_type_display()}"
    
class Staff(models.Model):
    staff_id = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    email = models.EmailField(unique=True)
    mobile_number = models.CharField(
        max_length=15, 
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$', 
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )
    is_registered = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    def _str_(self):
        return f"{self.staff_id}"

class StudentPassword(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student')
    ]

    identifier = models.CharField(max_length=20)  # roll_number or staff_id
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    password_hash = models.CharField(max_length=255)
    salt = models.CharField(max_length=255)  # Optional if you use Django's password hashers
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('identifier', 'role')

    def __str__(self):
        return f"{self.role.capitalize()} - {self.identifier}"
    
class StaffPassword(models.Model):
    ROLE_CHOICES = [
        ('staff', 'Staff')
    ]

    identifier = models.CharField(max_length=20)  # roll_number or staff_id
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    password_hash = models.CharField(max_length=255)
    salt = models.CharField(max_length=255)  # Optional if you use Django's password hashers
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('identifier', 'role')

    def __str__(self):
        return f"{self.role.capitalize()} - {self.identifier}"
    

from django.db import models
from django.conf import settings
from datetime import datetime, timedelta

class UserSession(models.Model):
    session_id = models.CharField(max_length=64, unique=True)
    user_id = models.IntegerField()
    user_type = models.CharField(max_length=10)  # 'student' or 'staff'
    access_token = models.TextField()
    refresh_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_sessions'
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['user_id']),
            models.Index(fields=['user_type']),
        ]

from django.db import models
from django.utils import timezone

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], default='medium')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']


class AnnouncementImage(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='announcement_images/')
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Image for {self.announcement.title}"
    
    class Meta:
        ordering = ['order']


# models.py
from django.db import models

class Event(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class EventImage(models.Model):
    event = models.ForeignKey(Event, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='events/')
    caption = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"Image for {self.event.name}"


# models.py
from django.db import models

class Facultylist(models.Model):
    name = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    email = models.EmailField()
    photo = models.ImageField(upload_to='faculty_photos/')
    
    class Meta:
        verbose_name_plural = "Faculty Members"
    
    def __str__(self):
        return self.name