from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.core.mail import send_mail
from .models import PassengerProfile
import re

GENDER_CHOICES = [
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
]

USERNAME_VALIDATOR = RegexValidator(
    regex=r'^(?![._])[a-zA-Z0-9._]{4,20}(?<![._])$',
    message='Username must be 4–20 characters, can include letters, numbers, dot, underscore. Cannot start/end with dot/underscore.'
)

class PassengerRegisterForm(forms.ModelForm):
    username = forms.CharField(
        max_length=20,
        validators=[USERNAME_VALIDATOR],
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Username"
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label="Email"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirm Password"
    )
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Gender"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists.")
        if '..' in username or '__' in username:
            raise ValidationError("Username cannot contain consecutive dots or underscores.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already registered.")
        return email

    def clean_password(self):
        password = self.cleaned_data['password']
        # Check length
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        # Check for uppercase, lowercase, digit, special character
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must contain at least one digit.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError("Password must contain at least one special character.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data["password"]
        gender = self.cleaned_data["gender"]

        user.set_password(password)
        if commit:
            user.save()
            PassengerProfile.objects.create(user=user, gender=gender)

            # Send welcome email
            send_mail(
                subject='SmartCoach Registration Successful',
                message=f'Hi {user.username},\n\nYou have successfully registered on SmartCoach.\n\nYour credentials:\nUsername: {user.username}\nPassword: {password}\n\nPlease keep them safe.',
                from_email='noreply@smartcoach.com',
                recipient_list=[user.email],
                fail_silently=False,
            )

        return user


from django import forms
from django.contrib.auth.models import User, Group

class MaintenanceStaffRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            staff_group, created = Group.objects.get_or_create(name='Maintenance Staff')
            user.groups.add(staff_group)
        return user
