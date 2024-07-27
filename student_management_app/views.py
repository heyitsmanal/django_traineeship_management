from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import login, logout
from django.http import HttpResponse, HttpResponseRedirect
import random
import string
from django.core.mail import send_mail
from django.conf import settings
from .forms import  EnrollStudentForm
from .models import Courses, CustomUser, Students
from .EmailBackEnd import EmailBackEnd  # Assuming you have a custom backend

def homepage(request):
    return render(request, 'homepage.html')

def loginPage(request):
    return render(request, 'login.html')



def generate_password(length=8):
    """Generate a random password."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))














def enroll_student(request):
    if request.method == 'POST':
        form = EnrollStudentForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            
            # Check if username or email already exists
            if CustomUser.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
                return redirect('enroll_student')
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "Email already exists.")
                return redirect('enroll_student')

            # Create user with username as password
            user = CustomUser.objects.create(
                username=username,
                email=email,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                user_type=3  # Assuming 3 corresponds to a student
            )
            user.set_password(username)  # Set username as password
            user.save()

            # Create student profile
            student = user.students
            student.gender = form.cleaned_data['gender']
            student.profile_pic = form.cleaned_data['profile_pic']
            student.address = form.cleaned_data['address']
            student.preferred_category = form.cleaned_data['preferred_category']
            student.grade = form.cleaned_data['grade']
            student.code_PPR = form.cleaned_data['code_PPR']
            student.save()

            # Enroll the student in all courses
            all_courses = Courses.objects.all()
            student.courses.set(all_courses)
            student.save()

            # Inform the user about their credentials
            messages.success(request, f"Student Enrolled Successfully! "
                                      f"Username: {username} and Password: {username}. "
                                      f"Please change your password after logging in.")
            return redirect('enroll_success')
    else:
        form = EnrollStudentForm()

    return render(request, 'Enroll.html', {'form': form})

def enroll_success(request):
    messages.success(request, f"you Enrolled Successfully! "
                         f"Username: {username} and Password: {username}. " #type:ignore
                         f"Please change your password after logging in.")
    return redirect('enroll_success')




def doLogin(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        user = EmailBackEnd.authenticate(request, username=request.POST.get('email'), password=request.POST.get('password'))
        if user is not None:
            login(request, user)
            user_type = user.user_type
            if user_type == '1':
                return redirect('admin_home')
            elif user_type == '2':
                return redirect('staff_home')
            elif user_type == '3':
                return redirect('student_home')
            else:
                messages.error(request, "Invalid Login!")
                return redirect('login')
        else:
            messages.error(request, "Invalid Login Credentials!")
            return redirect('login')

def get_user_details(request):
    if request.user.is_authenticated:
        return HttpResponse(f"User: {request.user.email} User Type: {request.user.user_type}")
    else:
        return HttpResponse("Please Login First")

def logout_user(request):
    logout(request)
    return HttpResponseRedirect('/')
