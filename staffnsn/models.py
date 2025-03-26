from django.db import models
from  studentnsn.models import Academics, PersonalInformation
class StudentsAttendance(models.Model):
    class CurrentSemester(models.TextChoices):
        SEM1 = '1', '1'
        SEM2 = '2', '2'
        SEM3 = '3', '3'
        SEM4 = '4', '4'
        SEM5 = '5', '5'
        SEM6 = '6', '6'
        SEM7 = '7', '7'
        SEM8 = '8', '8'
        SEM9 = '9', '9'
        SEM10 = '10', '10'
    roll_number = models.BigIntegerField()
    semester = models.CharField(max_length=2, choices=CurrentSemester.choices,default=CurrentSemester.SEM1 )
    staff_name = models.TextField()
    Course_Code = models.TextField()
    Course_Name = models.CharField(max_length=100)
    Date_Attended = models.DateField()
    From_Time = models.TimeField()
    To_Time = models.TimeField()
    No_of_Hours = models.SmallIntegerField()
    Is_Present = models.BooleanField(default=False)  

class AttendancePercentage(models.Model): 
    roll_number = models.BigIntegerField()
    Semester = models.IntegerField()
    Course_Code = models.TextField(null=True, blank=True)  # Null for full course calculation
    Attendance_Percentage = models.FloatField()


class Faculty(models.Model):
    DESIGNATION_CHOICES = [
        ('PROFESSOR', 'Professor'),
        ('ASSOCIATE PROFESSOR', 'Associate Professor'),
        ('ASSISTANT PROFESSOR', 'Assistant Professor'),
        # Add other designations as neede
    ]
    
    staff_id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=100)
    designation = models.CharField(max_length=50, choices=DESIGNATION_CHOICES)
    department = models.CharField(max_length=100)
    qualification = models.TextField()
    specialization = models.TextField()
    date_of_birth = models.DateField()
    date_of_joining = models.DateField()
    
    # Address fields
    present_address = models.TextField()
    contact_number = models.CharField(max_length=15)
    email = models.EmailField()
    
    # Experience fields
    teaching_research_experience = models.IntegerField(default=0)
    industry_experience = models.IntegerField(default=0)
    
    def _str_(self):
        return f"{self.name} ({self.staff_id})"


class ResearchGuidance(models.Model):
    DISCIPLINE_CHOICES = [
        ('M.Phil', 'M.Phil'),
        ('M.E', 'M.E'),
        ('M.Sc', 'M.Sc'),
        ('Ph.D', 'Ph.D'),
    ]
    
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='research_guidance')
    discipline = models.CharField(max_length=20, choices=DISCIPLINE_CHOICES)
    awarded = models.IntegerField(default=0)
    guidance = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('faculty', 'discipline')


class AcademicEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ('CONFERENCE_NATIONAL', 'Conference - National'),
        ('CONFERENCE_INTERNATIONAL', 'Conference - International'),
        ('SEMINAR', 'Seminar'),
        ('SYMPOSIA', 'Symposia'),
        ('WORKSHOP', 'Workshop'),
    ]
    
    ROLE_CHOICES = [
        ('ATTENDED', 'Attended'),
        ('CONDUCTED', 'Conducted'),
    ]
    
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='academic_events')
    event_type = models.CharField(max_length=25, choices=EVENT_TYPE_CHOICES)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    count = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('faculty', 'event_type', 'role')


class ResearchProject(models.Model):
    STATUS_CHOICES = [
        ('COMPLETED', 'Completed'),
        ('ONGOING', 'Ongoing'),
    ]
    
    PROJECT_TYPE_CHOICES = [
        ('MAJOR', 'Major'),
        ('MINOR', 'Minor'),
    ]
    
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='research_projects')
    project_title = models.CharField(max_length=255)
    project_type = models.CharField(max_length=5, choices=PROJECT_TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    def _str_(self):
        return self.project_title
class Publication(models.Model):
    TYPE_CHOICES = [
        ('JOURNAL_INTERNATIONAL', 'Journal - International'),
        ('JOURNAL_NATIONAL', 'Journal - National'),
        ('CONFERENCE_INTERNATIONAL', 'Conference - International'),
        ('CONFERENCE_NATIONAL', 'Conference - National'),
        ('BOOK', 'Book'),
        ('POPULAR_ARTICLE', 'Popular Article'),
    ]
    
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='publications')
    publication_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    authors = models.TextField()  # Comma-separated list of authors
    title = models.TextField()
    journal_name = models.CharField(max_length=255)
    volume = models.CharField(max_length=20, null=True, blank=True)
    number = models.CharField(max_length=20, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    pages = models.CharField(max_length=20, null=True, blank=True)
    year = models.IntegerField()
    
    def _str_(self):
        return self.title

class Award(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='awards')
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    
    def _str_(self):
        return self.name


class PublicationCategory(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='publication_categories')
    journal_national = models.IntegerField(default=0)
    journal_international = models.IntegerField(default=0)
    conference_national = models.IntegerField(default=0)
    conference_international = models.IntegerField(default=0)
    books_published = models.IntegerField(default=0)
    popular_articles = models.IntegerField(default=0)