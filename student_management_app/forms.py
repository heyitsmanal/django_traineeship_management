from django import forms 
from student_management_app.models import Courses, Group,Project, Students,Group, Day



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
    class Meta:
        model = Group
        fields = ['days_of_week', 'category']

    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        self.fields['days_of_week'].widget = forms.CheckboxSelectMultiple()
        self.fields['days_of_week'].queryset = Day.objects.all()












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