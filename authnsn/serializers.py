from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Student, Staff, StudentPassword,StaffPassword

# Custom Serializer for Login
class LoginSerializer(serializers.Serializer):
    # Only require staff_id and password for staff login
    roll_number = serializers.CharField(max_length=20, required=False)  # For student login
    student_type = serializers.CharField(max_length=20, required=False)  # For student login
    staff_id = serializers.CharField(max_length=20, required=False)  # For staff login
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        # Ensure either student or staff login is attempted, not both
        if not data.get('roll_number') and not data.get('staff_id'):
            raise serializers.ValidationError("Either roll_number (for student) or staff_id (for staff) must be provided.")
        return data


class RegisterSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True)

    # Fields for student registration
    roll_number = serializers.CharField(required=False)
    #previous_roll_number = serializers.CharField(required=False, allow_blank=True)
    course= serializers.ChoiceField(choices=['B.E', 'M.E', 'PhD'], required=False)

    # Fields for staff registration
    staff_id = serializers.CharField(required=False)

    def validate(self, data):
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if password != confirm_password:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        if 'roll_number' in data and 'staff_id' in data:
            raise serializers.ValidationError("Provide either roll_number for students or staff_id for staff, not both.")

        if 'roll_number' not in data and 'staff_id' not in data:
            raise serializers.ValidationError("Either roll_number or staff_id must be provided.")

        return data

    def create(self, validated_data):
        raise NotImplementedError("This serializer should not be used for object creation.")

# Custom Serializer for Profile (to get user data)
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentPassword, StaffPassword# Or any other model you're using for user data
        fields = ('username', 'email', 'role')  # Add the necessary fields for your profile
