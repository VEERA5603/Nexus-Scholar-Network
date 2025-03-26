from django.db import models
from django.core.exceptions import ValidationError

class Address(models.Model):
    AREA_TYPE_CHOICES = [
        ('Urban', 'Urban'),
        ('Rural', 'Rural'),
    ]
    area_type = models.CharField(max_length=10, choices=AREA_TYPE_CHOICES)
    door_number = models.TextField()
    apartment_name = models.CharField(max_length=35, null=True, blank=True)
    street_name = models.CharField(max_length=35)
    taluk = models.CharField(max_length=35)
    block = models.CharField(max_length=35)
    district = models.CharField(max_length=35)
    state = models.CharField(max_length=35)
    pincode = models.BigIntegerField()

    def __str__(self):
        return f"{self.door_number}, {self.street_name}, {self.taluk}, {self.district}, {self.state} - {self.pincode}"

class PersonalInformation(models.Model):
    STUDENT_TYPE_CHOICES = [
        (0, 'Regular'),
        (1, 'Lateral Entry'),
        (2, 'Rejoin'),
    ]
    
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    
    SPECIAL_QUOTA_CHOICES = [
        ('0', 'None'),
        ('1', 'Special Quota'),
    ]
    
    roll_number = models.BigIntegerField(primary_key=True)
    previous_roll_number = models.BigIntegerField(unique=True, null=True, blank=True)
    type_of_student = models.PositiveSmallIntegerField(choices=STUDENT_TYPE_CHOICES)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    dob = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=5)
    religion = models.CharField(max_length=50)
    community = models.CharField(max_length=50)
    caste = models.CharField(max_length=50)
    nationality = models.CharField(max_length=50)
    student_mobile = models.BigIntegerField()
    email = models.EmailField(unique=True)
    aadhar_number = models.BigIntegerField(unique=True)
    father_name = models.CharField(max_length=100)
    father_occupation = models.CharField(max_length=100)
    mother_name = models.CharField(max_length=100)
    mother_occupation = models.CharField(max_length=100)
    father_mobile = models.BigIntegerField()
    mother_mobile = models.BigIntegerField()
    annual_income = models.DecimalField(max_digits=10, decimal_places=2)
    height = models.FloatField()
    weight = models.FloatField()
    differentially_abled = models.BooleanField()
    Type_of_disability = models.CharField(max_length=100,blank=True, null=True)
    special_quota = models.CharField(max_length=1, choices=SPECIAL_QUOTA_CHOICES, null=True, blank=True)
    permanent_address = models.ForeignKey(Address, related_name="permanent_address", on_delete=models.CASCADE)
    communication_address = models.ForeignKey(Address, related_name="communication_address", on_delete=models.CASCADE)

    def clean(self):
        if self.type_of_student != 2 and self.previous_roll_number is not None:
            raise ValidationError("Previous roll number is only applicable for rejoin students.")
        if self.type_of_student == 2 and self.previous_roll_number is None:
            raise ValidationError("Rejoin students must have a previous roll number.")
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.roll_number})"
    
class BriefDetails(models.Model):
    roll_number = models.OneToOneField(
        PersonalInformation, 
        on_delete=models.CASCADE, 
        db_column='roll_number', 
        primary_key=True
    )
    identification_marks = models.TextField()
    extracurricular_activities = models.TextField()
    brother_name = models.CharField(max_length=100)
    brother_mobile = models.CharField(max_length=20)
    sister_names = models.TextField(null=True, blank=True)
    sister_mobile = models.CharField(max_length=20)
    friends_names = models.TextField()
    friends_mobile = models.TextField()
    having_vehicle = models.BooleanField(default=False)
    vehicle_number = models.CharField(max_length=20)
    any_health_issues = models.TextField()
    hobbies = models.TextField()

    class Meta:
        db_table = 'brief_details'
    def _str_(self):
        return f"{self.roll_number.roll_number}"
    
class RejoinStudent(models.Model):
    roll_number = models.OneToOneField(
        PersonalInformation, 
        on_delete=models.CASCADE, 
        db_column='roll_number', 
        primary_key=True
    )
    new_roll_number = models.BigIntegerField(unique=True)
    previous_type_of_student = models.CharField(
        max_length=10,
        choices=[('Regular', 'regular'), ('Lateral', 'lateral')]
    ) # 2 for Rejoin
    year_of_discontinue = models.DateField()
    year_of_rejoin = models.DateField()
    reason_for_discontinue = models.TextField()

    class Meta:
        db_table = 'rejoin_student'
    def _str_(self):
        return f"{self.roll_number.roll_number}"
    

class Hosteller(models.Model):
    roll_number = models.OneToOneField(
        PersonalInformation, 
        on_delete=models.CASCADE, 
        db_column='roll_number', 
        primary_key=True
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    hostel_name = models.CharField(max_length=100)
    hostel_address = models.TextField()
    from_date = models.DateField()
    to_date = models.DateField(null=True, blank=True)
    room_number = models.IntegerField()

    # Foreign key constraint linking to PersonalInformation model

    class Meta:
        db_table = 'hosteller'
    def _str_(self):
        return f"{self.roll_number.roll_number}"
    
class BankDetails(models.Model):
    roll_number = models.OneToOneField(
        PersonalInformation, 
        on_delete=models.CASCADE, 
        db_column='roll_number', 
        primary_key=True
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    account_number = models.BigIntegerField()
    branch = models.CharField(max_length=75)
    ifsc = models.TextField()
    micr = models.BigIntegerField()
    account_type = models.CharField(
        max_length=10,
        choices=[('Savings', 'Savings'), ('Current', 'Current')]
    )
    address = models.TextField()
    pan_number = models.CharField(max_length=35)

    class Meta:
        db_table = 'bank_details'
    def _str_(self):
        return f"{self.roll_number.roll_number}"
    
class Scholarship(models.Model):
    roll_number = models.ForeignKey('PersonalInformation', on_delete=models.CASCADE)
    scholarship_type = models.CharField(
        max_length=50,
        choices=[
            ('Pudhumai Penn', 'Pudhumai Penn'),
            ('Naan Mudhalvan', 'Naan Mudhalvan'),
            ('7.5 Special Quota', '7.5 Special Quota'),
            ('Post Matric (BC/MBC)', 'Post Matric (BC/MBC)'),
            ('SC/ST', 'SC/ST'),
            ('First Graduate', 'First Graduate')
        ]
    )
    academic_year_availed = models.IntegerField()
    amount = models.BigIntegerField(default=0)
    availed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'scholarship'
        
    def __str__(self):
        return f"{self.roll_number.roll_number} - {self.scholarship_type}"

class Academics(models.Model):
    class Course(models.TextChoices):
        BE = 'B.E', 'B.E'
        ME = 'M.E', 'M.E'
        PHD = 'PhD', 'PhD'

    class CurrentYear(models.TextChoices):
        FIRST = '1', '1'
        SECOND = '2', '2'
        THIRD = '3', '3'
        FOURTH = '4', '4'
        FIFTH = '5', '5'
        SIXTH = '6', '6'

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

    roll_number = models.OneToOneField(
        PersonalInformation, 
        on_delete=models.CASCADE, 
        db_column='roll_number', 
        primary_key=True
    )
    course = models.CharField(max_length=5, choices=Course.choices)
    department = models.CharField(max_length=100)
    current_year = models.CharField(max_length=1, choices=CurrentYear.choices)
    current_semester = models.CharField(max_length=2, choices=CurrentSemester.choices)
    year_joining = models.DateField()
    type_of_admission = models.CharField(max_length=50)
    admission_type = models.CharField(max_length=50)
    emis_number = models.BigIntegerField()
    umis_number = models.BigIntegerField()
    class_incharge = models.CharField(max_length=50)
    class_room_number = models.SmallIntegerField()

    class Meta:
        db_table = 'Academics'

    def _str_(self):
        return f"{self.roll_number.roll_number} - {self.course}"



class PersonalDocuments(models.Model):
    roll_number = models.OneToOneField(
        PersonalInformation, 
        on_delete=models.CASCADE, 
        db_column='roll_number', 
        primary_key=True
    )
    student_photo = models.ImageField(upload_to='documents/student_photos/')
    university_id = models.ImageField(upload_to='documents/university_ids/')
    sslc_certificate = models.ImageField(upload_to='documents/sslc_certificates/')
    hsc_certificate = models.ImageField(upload_to='documents/hsc_certificates/', blank=True, null=True)
    community_certificate = models.ImageField(upload_to='documents/community_certificates/')
    nativity_certificate = models.ImageField(upload_to='documents/nativity_certificates/', blank=True, null=True)
    transfer_certificate = models.ImageField(upload_to='documents/transfer_certificates/')
    twelfth_marksheet = models.ImageField(upload_to='documents/12th_marksheets/')
    tenth_marksheet = models.ImageField(upload_to='documents/10th_marksheets/')
    aadhar = models.ImageField(upload_to='documents/aadhar/')
    pan_card = models.ImageField(upload_to='documents/pan_cards/', blank=True, null=True)
    driving_license = models.ImageField(upload_to='documents/driving_licenses/', blank=True, null=True)
    first_graduate = models.ImageField(upload_to='documents/first_graduates/', blank=True, null=True)
    bank_passbook = models.ImageField(upload_to='documents/bank_passbooks/', blank=True, null=True)
    tnea_provisional = models.ImageField(upload_to='documents/tnea_provisionals/')
    differentially_abled_certificate = models.ImageField(upload_to='documents/differentially_abled_certificates/', blank=True, null=True)
    income_certificate = models.ImageField(upload_to='documents/income_certificates/', blank=True, null=True)
    diploma_certificate = models.ImageField(upload_to='documents/diploma_certificates/', blank=True, null=True)

    class Meta:
        db_table = 'personal_documents'

    def _str_(self):
        return f"{self.roll_number.roll_number}"
from django.db import models

class Examination(models.Model):
    SEMESTER_CHOICES = [
        ('1', 'Semester 1'),
        ('2', 'Semester 2'),
        ('3', 'Semester 3'),
        ('4', 'Semester 4'),
        ('5', 'Semester 5'),
        ('6', 'Semester 6'),
        ('7', 'Semester 7'),
        ('8', 'Semester 8'),
        ('9', 'Semester 9'),
        ('10', 'Semester 10'),
    ]
    
    roll_number = models.BigIntegerField()
    register_number = models.BigIntegerField()
    semester = models.CharField(max_length=2, choices=SEMESTER_CHOICES)
    course_code = models.TextField()
    course_name = models.CharField(max_length=100)
    internal_mark = models.PositiveSmallIntegerField()
    grade = models.CharField(max_length=2)
    credit_hours = models.FloatField()
    grade_point = models.FloatField()
    credit_point = models.FloatField()
    exam_held_on = models.DateField()
    regulations = models.TextField()

    # ForeignKey to Personal_Information table (assuming that table is already created)
    

    class Meta:
        db_table = 'examinations'

    def __str__(self):
        return f"Examination for {self.register_number} - {self.semester}"


class SSLC(models.Model):
    roll_number = models.OneToOneField(PersonalInformation, on_delete=models.CASCADE, primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    school_name = models.TextField()
    school_address = models.TextField()
    board = models.TextField()
    sslc_register = models.BigIntegerField(unique=True)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    sslc_percentage = models.FloatField()
    passed_year = models.PositiveSmallIntegerField()
    emis_number = models.BigIntegerField()
    def _str_(self):
        return f"{self.roll_number.roll_number}"

class SSLCMarks(models.Model):
    roll_number = models.BigIntegerField()
    sslc_register = models.BigIntegerField()
    subject_name = models.CharField(max_length=100)
    subject_mark = models.FloatField()
    def _str_(self):
        return f"{self.roll_number.roll_number}"


class HSC(models.Model):
    roll_number = models.OneToOneField(PersonalInformation, on_delete=models.CASCADE, primary_key=True)
    hsc_register = models.BigIntegerField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    school_name = models.TextField()
    school_address = models.TextField()
    board = models.TextField()
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    hsc_percentage = models.FloatField()
    passed_year = models.PositiveSmallIntegerField()
    emis_number = models.BigIntegerField()
    def _str_(self):
        return f"{self.roll_number.roll_number}"


class HSCMarks(models.Model):
    roll_number = models.BigIntegerField()
    hsc_register = models.BigIntegerField()
    subject_name = models.CharField(max_length=100)
    subject_mark = models.FloatField()
    def _str_(self):
        return f"{self.roll_number.roll_number}"
    
class DiplomaStudent(models.Model):
    roll_number = models.OneToOneField(PersonalInformation, on_delete=models.CASCADE, primary_key=True)
    diploma_register = models.BigIntegerField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    sslc_register = models.BigIntegerField(unique=True)
    hsc_register = models.BigIntegerField(unique=True,blank=True, null=True)
    course_name = models.CharField(max_length=100)
    college_name = models.TextField()
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    year_of_joined = models.DateField()
    year_of_passed = models.DateField()

    class Meta:
        db_table = 'diploma_students'
    def _str_(self):
        return f"{self.roll_number.roll_number}"
    
class DiplomaMark(models.Model):
    diploma_register = models.BigIntegerField()
    roll_number = models.BigIntegerField()
    semester = models.CharField(
        max_length=1,
        choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6')]
    )
    course_name = models.CharField(max_length=100)
    course_mark = models.SmallIntegerField()

    class Meta:
        db_table = 'diploma_mark'
    def _str_(self):
        return f"{self.roll_number.roll_number}"
    
class SemesterMarksheet(models.Model):
    SEMESTER_NUMBER_CHOICES = [(i, str(i)) for i in range(1, 11)]

    roll_number = models.BigIntegerField()
    register_number = models.BigIntegerField()
    semester = models.PositiveSmallIntegerField(choices=SEMESTER_NUMBER_CHOICES)
    marksheet = models.ImageField(upload_to="marksheets/")  # Assuming it's an image; change to FileField if it's a general file.
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "Semester_Marksheet"  # Use the same table name as in your SQL definition
    def _str_(self):
        return f"{self.roll_number.roll_number}"
    
class DiplomaMarksheet(models.Model):
    SEMESTER_NUMBER_CHOICES = [(i, str(i)) for i in range(1, 7)]

    roll_number = models.BigIntegerField()
    register_number = models.BigIntegerField()
    semester = models.PositiveSmallIntegerField(choices=SEMESTER_NUMBER_CHOICES)
    marksheet = models.ImageField(upload_to="marksheets/diploma")  # Assuming it's an image; change to FileField if it's a general file.
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "Diploma_Marksheet"  # Use the same table name as in your SQL definition
    def _str_(self):
        return f"{self.roll_number.roll_number}"
    
    