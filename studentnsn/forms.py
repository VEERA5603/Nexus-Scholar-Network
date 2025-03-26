from django import forms
from .models import PersonalInformation, Address

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = '__all__'

class PersonalInformationForm(forms.ModelForm):
    class Meta:
        model = PersonalInformation
        exclude = ['roll_number']
