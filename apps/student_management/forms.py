from django import forms 
from apps.student_management.models import Courses, CustomUser, Group,Project, Students,Group, Day
from student_management_system import settings


class DateInput(forms.DateInput):
    input_type = "date"



class AddStudentForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=50, widget=forms.EmailInput(attrs={"class": "form-control"}))
    password = forms.CharField(label="Password", max_length=50, widget=forms.PasswordInput(attrs={"class": "form-control"}))
    first_name = forms.CharField(label="First Name", max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(label="Last Name", max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))
    username = forms.CharField(label="Username", max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))
    address = forms.CharField(label="Address", max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))
    gender = forms.ChoiceField(label="Gender", choices=(('Male', 'Male'), ('Female', 'Female')), widget=forms.Select(attrs={"class": "form-control"}))
    profile_pic = forms.FileField(label="Profile Pic", required=False, widget=forms.FileInput(attrs={"class": "form-control"}))
    grade = forms.ChoiceField(label="Grade", choices=[
        ('primaire', 'Primaire'),
        ('college', 'Collège'),
        ('lycee', 'Lycée'),
        ('universite', 'Université'),
        ('superieure', 'Supérieure')
    ], widget=forms.Select(attrs={"class": "form-control"}))
    code_PPR = forms.CharField(label="Code PPR", max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))
    reference = forms.CharField(label="Refrence", max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))
    preferred_category = forms.ChoiceField(label="Preferred Category", choices=[
        ('morning', 'Morning'),
        ('evening', 'Evening')
    ], widget=forms.Select(attrs={"class": "form-control"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
       

class EditStudentForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=50, widget=forms.EmailInput(attrs={"class": "form-control"}))
    first_name = forms.CharField(label="First Name", max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(label="Last Name", max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))
    username = forms.CharField(label="Username", max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))
    address = forms.CharField(label="Address", max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))
    gender = forms.ChoiceField(label="Gender", choices=(('Male', 'Male'), ('Female', 'Female')), widget=forms.Select(attrs={"class": "form-control"}))
    profile_pic = forms.FileField(label="Profile Pic", required=False, widget=forms.FileInput(attrs={"class": "form-control"}))
    grade = forms.ChoiceField(label="Grade", choices=[
        ('primaire', 'Primaire'),
        ('college', 'Collège'),
        ('lycee', 'Lycée'),
        ('universite', 'Université'),
        ('superieure', 'Supérieure')
    ], widget=forms.Select(attrs={"class": "form-control"}))
    code_PPR = forms.CharField(label="Code PPR", max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))
    reference = forms.CharField(label="Refrence", max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))
    preferred_category = forms.ChoiceField(label="Preferred Category", choices=[
        ('morning', 'Morning'),
        ('evening', 'Evening')
    ], widget=forms.Select(attrs={"class": "form-control"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
  
   


class GroupForm(forms.ModelForm):
    DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    class Meta:
        model = Group
        fields = ['days_of_week', 'category']

    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        self.fields['days_of_week'].widget = forms.CheckboxSelectMultiple()

        # Check if the Day model has entries, if not, use the predefined list
        if not Day.objects.exists():
            self.fields['days_of_week'].choices = self.DAYS_OF_WEEK
        else:
            self.fields['days_of_week'].queryset = Day.objects.all()

        # Only apply the class to the surrounding div to avoid duplication in the HTML
        self.fields['days_of_week'].widget.attrs.update({'class': 'form-check-input'})



class GroupingForm(forms.Form):
    MAX_GROUP_CHOICES = [(i, str(i)) for i in range(1, 11)]  # Choices from 1 to 10
    MAX_SALLE_CHOICES = [(i, str(i)) for i in range(1, 21)]  # Choices from 1 to 20 for room availability

    max_groups_morning = forms.ChoiceField(
        required=False,
        initial=5,
        label='Maximum Morning Groups',
        choices=MAX_GROUP_CHOICES,
        widget=forms.Select(attrs={'class': 'select-days'})
    )
    
    max_groups_evening = forms.ChoiceField(
        required=False,
        initial=5,
        label='Maximum Evening Groups',
        choices=MAX_GROUP_CHOICES,
        widget=forms.Select(attrs={'class': 'select-days'})
    )
    
    avoid_days = forms.MultipleChoiceField(
        required=False,
        label='Avoid Days',
        choices=[(i, day) for i, day in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])],
        widget=forms.SelectMultiple(attrs={'class': 'select-days-multiple'})
    )
    
    create_days = forms.MultipleChoiceField(
        required=False,
        label='Create Days',
        choices=[(i, day) for i, day in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])],
        widget=forms.SelectMultiple(attrs={'class': 'select-days-multiple'})
    )

    max_salle_disponible = forms.ChoiceField(
        required=True,
        initial=10,
        label='Maximum Available Rooms',
        choices=MAX_SALLE_CHOICES,
        widget=forms.Select(attrs={'class': 'select-days'})
    )



class CustomStudentChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.admin.last_name}, {obj.admin.first_name}"


class ProjectValidationForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'student']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter project title'}),
            'student': forms.Select(attrs={'class': 'form-control'}),
        }

    student = CustomStudentChoiceField(
        queryset=Students.objects.all(),
        required=True
    )

    
class EnrollStudentForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=50, widget=forms.EmailInput(attrs={"class": "form-control"}))
    password = forms.CharField(label="Password", max_length=50, widget=forms.PasswordInput(attrs={"class": "form-control"}))
    first_name = forms.CharField(label="First Name", max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(label="Last Name", max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))
    username = forms.CharField(label="Username", max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))
    address = forms.CharField(label="Address", max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))
    gender = forms.ChoiceField(label="Gender", choices=(('Male', 'Male'), ('Female', 'Female')), widget=forms.Select(attrs={"class": "form-control"}))
    profile_pic = forms.FileField(label="Profile Pic", required=False, widget=forms.FileInput(attrs={"class": "form-control"}))
    grade = forms.ChoiceField(label="Grade", choices=[
        ('primaire', 'Primaire'),
        ('college', 'Collège'),
        ('lycee', 'Lycée'),
        ('universite', 'Université'),
        ('superieure', 'Supérieure')
    ], widget=forms.Select(attrs={"class": "form-control"}))
    code_PPR = forms.CharField(label="Code PPR", max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))
    reference = forms.CharField(label="Reference", max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))
    preferred_category = forms.ChoiceField(label="Preferred Category", choices=[
        ('morning', 'Morning'),
        ('evening', 'Evening')
    ], widget=forms.Select(attrs={"class": "form-control"}))













from django import forms
from django.contrib.auth.forms import  PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext as _


class CustomPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        """Given an email, return matching user(s) who should receive a reset."""
        return CustomUser.objects.filter(email__iexact=email)
    def send_mail(self, subject_template_name, email_template_name,
              context, from_email, to_email, html_email_template_name=None):
        print(f"Attempting to send email to: {to_email}")  # Debugging line
        print('from_email',from_email)
        if CustomUser.objects.filter(email__iexact=to_email).exists():
            print(f"Sending email to: {to_email}")  # Debugging line
            super().send_mail(
                subject_template_name, email_template_name,
                context, from_email, to_email, html_email_template_name
            )
    def save(self, domain_override=None, subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html', use_https=False,
             token_generator=default_token_generator, from_email=None, request=None,
             html_email_template_name=None, extra_email_context=None):
        """
        Generate a one-use only link for resetting password and send it to the
        user.
        """
        email = self.cleaned_data["email"]
        
        users = self.get_users(email)
        print('users',users)
        if not users:
            return False
        for user in users:
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            context = {
                'email': email,
                'domain': domain,
                'site_name': site_name,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
                **(extra_email_context or {}),
            }
            print('from_email',from_email)
            self.send_mail(
                subject_template_name, email_template_name, context, from_email,
                email, html_email_template_name=html_email_template_name,
            )
        return True





