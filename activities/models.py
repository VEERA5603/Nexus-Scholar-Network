from django.db import models

# Create your models here.
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class AcademicYear(models.Model):
    year = models.CharField(max_length=9, unique=True, help_text="Format: YYYY-YYYY")
    is_current = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-year']
    
    def __str__(self):
        return self.year

class DepartmentActivity(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Department Activities"
    
    def __str__(self):
        return f"{self.title} ({self.academic_year})"

class ActivityImage(models.Model):
    activity = models.ForeignKey(DepartmentActivity, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='activities/images/')
    caption = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"Image for {self.activity.title}"