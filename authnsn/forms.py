from django import forms

class StudentLoginForm(forms.Form):
    roll_number = forms.CharField()
    student_type = forms.ChoiceField(choices=[('regular', 'Regular'), ('lateral', 'Lateral')])
    password = forms.CharField(widget=forms.PasswordInput)

class StaffLoginForm(forms.Form):
    staff_id = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class RegisterForm(forms.Form):
    roll_number = forms.CharField()
    student_type = forms.ChoiceField(choices=[('regular', 'Regular'), ('lateral', 'Lateral')])
    password = forms.CharField(widget=forms.PasswordInput)
    staff_id = forms.CharField(required=False)  # For staff registration
