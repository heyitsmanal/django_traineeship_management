import random
from django.forms import Form
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.core.files.storage import FileSystemStorage #To upload Profile Picture
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction, IntegrityError
from django.http import HttpResponse
from django.template.loader import render_to_string
from .utils import generate_certificate
from django.urls import reverse
from django.db.models.signals import post_save




from student_management_app.models import BlacklistedStudent, CustomUser, Day, Group, GroupSchedule, Project, Staffs, Courses, Students, Attendance, AttendanceReport, group_created_handler
from .forms import AddStudentForm, EditStudentForm, EnrollStudentForm, GroupForm , GroupingForm

from django.shortcuts import render
 # Replace with your actual model

def search_view(request):
    query = request.GET.get('q', '')
    # Searching by username, first_name, and last_name
    results = CustomUser.objects.filter(
        username__icontains=query
    ) | CustomUser.objects.filter(
        first_name__icontains=query
    ) | CustomUser.objects.filter(
        last_name__icontains=query
    )
    return render(request, 'hod_template/search_results.html', {'results': results})

def admin_home(request):
    all_student_count = Students.objects.all().count()
    course_count = Courses.objects.all().count()
    staff_count = Staffs.objects.all().count()

    # Total Students in Each Course
    courses = Courses.objects.all()
    course_name_list = [course.course_name for course in courses]
    student_count_list_in_course = [Students.objects.filter(courses=course).count() for course in courses]  # Updated filter to use 'courses'

    # Total Students in Each Grade
    grades = ['primaire', 'college', 'lycee', 'universite', 'superieure']
    grade_name_list = grades
    student_count_list_in_grade = [Students.objects.filter(grade=grade).count() for grade in grades]

    # Attendance rate for each course
    course_attendance_data = []
    for course in courses:
        total_students = Students.objects.filter(courses=course).count()  # Updated filter to use 'courses'
        if total_students == 0:
            attendance_rate = 0
        else:
            # Get attendance records related to this course
            attendance_ids = Attendance.objects.filter(course=course).values_list('id', flat=True)
            total_attendance_days = Attendance.objects.filter(course=course).count()
            if total_attendance_days == 0:
                attendance_rate = 0
            else:
                attendance_present_count = AttendanceReport.objects.filter(status=True, attendance_id__in=attendance_ids).count()
                attendance_rate = (attendance_present_count / (total_students * total_attendance_days)) * 100  # Calculate attendance rate
        course_attendance_data.append({
            "course_name": course.course_name,
            "attendance_rate": attendance_rate
        })

    context = {
        "all_student_count": all_student_count,
        "course_count": course_count,
        "staff_count": staff_count,
        "course_name_list": course_name_list,
        "student_count_list_in_course": student_count_list_in_course,
        "grade_name_list": grade_name_list,
        "student_count_list_in_grade": student_count_list_in_grade,
        "course_attendance_data": course_attendance_data,
    }
    return render(request, "hod_template/home_content.html", context)



def add_staff(request):
    courses = Courses.objects.all()
    print(courses)
    context = {
        'courses': courses,
    }
    return render(request, 'hod_template/add_staff_template.html', context)



def add_staff_save(request):
    if request.method == 'POST':
        # Retrieve form data
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        gender = request.POST.get('gender')
        profile_pic = request.FILES.get('profile_pic')  # Handle file uploads
        course_id = request.POST.get('course')

        # Validate required fields
        if not (email and username and password and first_name and last_name and address and gender and course_id):
            messages.error(request, "All fields are required.")
            return redirect('add_staff')

        # Check if a user with the same username or email already exists
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('add_staff')
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('add_staff')

        try:
            # Fetch the Course object
            course = get_object_or_404(Courses, id=course_id)

            # Create the CustomUser instance
            user = CustomUser.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
                user_type=2  # Assuming 2 corresponds to a staff
            )
            user.set_password(password)
            user.save()

            # Set staff attributes via related Staffs model (handled by signal)
            staff = user.staffs
            staff.gender = gender
            staff.profile_pic = profile_pic
            staff.address = address
            staff.course = course
            staff.save()

            messages.success(request, "Staff Added Successfully!")
            return redirect('add_staff')

        except Courses.DoesNotExist:
            messages.error(request, "Course does not exist.")
        
        except Exception as e:
            messages.error(request, f"Failed to Add Staff: {str(e)}")

    else:
        messages.error(request, "Invalid Method")

    return redirect('add_staff')



def manage_staff(request):
    staffs = Staffs.objects.all()
    # for staff in staffs:
    #     print(f"Staff ID: {staff.id}, Profile Pic: {staff.profile_pic}")
    context = {
        "staffs": staffs
    }
    return render(request, "hod_template/manage_staff_template.html", context)



def edit_staff(request, staff_id):
    staff = Staffs.objects.get(admin=staff_id)
    courses = Courses.objects.all() 

    context = {
        "courses": courses,
        "staff": staff,
        "id": staff_id
    }
    return render(request, "hod_template/edit_staff_template.html", context)



def edit_staff_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        staff_id = request.POST.get('staff_id')
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        course_id = request.POST.get('course')
        gender = request.POST.get('gender')

        # Getting Profile Pic first
        if len(request.FILES) != 0:
            profile_pic = request.FILES['profile_pic']
            fs = FileSystemStorage()
            filename = fs.save(profile_pic.name, profile_pic)
            profile_pic_url = fs.url(filename)
        else:
            profile_pic_url = None

        try:
            # UPDATE CustomUser Model
            user = CustomUser.objects.get(id=staff_id)
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.username = username
            user.save()

            # Ensure the course ID exists
            try:
                course = Courses.objects.get(id=course_id)
            except Courses.DoesNotExist:
                messages.error(request, "Course does not exist.")
                return redirect('/edit_staff/' + str(staff_id))

            # UPDATE Staffs Model
            staff_model = Staffs.objects.get(admin=staff_id)
            staff_model.gender = gender
            if profile_pic_url is not None:
                    staff_model.profile_pic = profile_pic_url
            staff_model.address = address
            staff_model.course = course
            staff_model.save()

            messages.success(request, "Staff Updated Successfully.")
            return redirect('/edit_staff/' + str(staff_id))

        except Exception as e:
            # Log the exception
            print(f"Error: {e}")
            messages.error(request, f"Failed to Update Staff: {e}")
            return redirect('/edit_staff/' + str(staff_id))



def delete_staff(request, staff_id):
    staffs = Staffs.objects.filter(admin=staff_id)
    
    if staffs.exists():
        # Delete all matching staff entries
        staffs.delete()
        messages.success(request, "Staff(s) Deleted Successfully.")
    else:
        messages.error(request, "No Staff found to delete.")
        
    return redirect('manage_staff')



def add_course(request):
    return render(request, "hod_template/add_course_template.html")



def add_course_save(request):
    if request.method != "POST":
        messages.error(request, "Invalid Method!")
        return redirect('add_course')
    else:
        course = request.POST.get('course')
        try:
            course_model = Courses(course_name=course)
            course_model.save()
            messages.success(request, "Course Added Successfully!")
            return redirect('add_course')
        except:
            messages.error(request, "Failed to Add Course!")
            return redirect('add_course')



def manage_course(request):
    courses = Courses.objects.all()
    context = {
        "courses": courses
    }
    return render(request, 'hod_template/manage_course_template.html', context)



def edit_course(request, course_id):
    course = Courses.objects.get(id=course_id)
    context = {
        "course": course,
        "id": course_id
    }
    return render(request, 'hod_template/edit_course_template.html', context)



def edit_course_save(request):
    if request.method != "POST":
        HttpResponse("Invalid Method")
    else:
        course_id = request.POST.get('course_id')
        course_name = request.POST.get('course')

        try:
            course = Courses.objects.get(id=course_id)
            course.course_name = course_name
            course.save()

            messages.success(request, "Course Updated Successfully.")
            return redirect('/edit_course/'+course_id)

        except:
            messages.error(request, "Failed to Update Course.")
            return redirect('/edit_course/'+course_id)



def delete_course(request, course_id):
    course = Courses.objects.get(id=course_id)
    try:
        course.delete()
        messages.success(request, "Course Deleted Successfully.")
        return redirect('manage_course')
    except:
        messages.error(request, "Failed to Delete Course.")
        return redirect('manage_course')



def add_student(request):
    form = AddStudentForm()
    context = {
        "form": form
    }
    return render(request, 'hod_template/add_student_template.html', context)



def add_student_save(request):
    if request.method == 'POST':
        form = AddStudentForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            username = form.cleaned_data['username']
            address = form.cleaned_data['address']
            gender = form.cleaned_data['gender']
            profile_pic = form.cleaned_data['profile_pic']
            preferred_category = form.cleaned_data['preferred_category']
            grade = form.cleaned_data['grade']
            code_PPR = form.cleaned_data['code_PPR']

            # Check if a user with the same username or email already exists
            if CustomUser.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
                return redirect('add_student')
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "Email already exists.")
                return redirect('add_student')

            try:
                # Create the CustomUser instance
                user = CustomUser.objects.create(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    user_type=3  # Assuming 3 corresponds to a student
                )
                user.set_password(password)
                user.save()

                # Fetch the created Students instance and update its fields
                student = user.students
                student.gender = gender
                student.profile_pic = profile_pic
                student.address = address
                student.preferred_category = preferred_category
                student.grade = grade
                student.code_PPR = code_PPR
                student.save()

                # Automatically enroll the student in all existing courses
                all_courses = Courses.objects.all()
                student.courses.set(all_courses)
                student.save()

                messages.success(request, "Student Added and Enrolled in All Courses Successfully!")
                return redirect('add_student')
            
            except Exception as e:
                messages.error(request, f"Failed to Add Student: {str(e)}")

        else:
            messages.error(request, "Form is not valid.")
    else:
        form = AddStudentForm()

    context = {
        'form': form,
    }
    return render(request, 'hod_template/add_student_template.html', context)



def manage_student(request):
    students = Students.objects.select_related('admin').all()
    context = {
        "students": students
    }
    return render(request, 'hod_template/manage_student_template.html', context)



def edit_student(request, student_id):
    request.session['student_id'] = student_id

    try:
        student = Students.objects.get(admin=student_id)
    except Students.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect('manage_student')

    form = EditStudentForm()
    form.fields['email'].initial = student.admin.email
    form.fields['username'].initial = student.admin.username
    form.fields['first_name'].initial = student.admin.first_name
    form.fields['last_name'].initial = student.admin.last_name
    form.fields['address'].initial = student.address
    form.fields['gender'].initial = student.gender
    form.fields['grade'].initial = student.grade
    form.fields['code_PPR'].initial = student.code_PPR
    form.fields['reference'].initial = student.reference
  


    context = {
        "id": student_id,
        "username": student.admin.username,
        "form": form
    }
    return render(request, "hod_template/edit_student_template.html", context)



def edit_student_save(request):
    if request.method != "POST":
        return HttpResponse("Invalid Method!")
    else:
        student_id = request.session.get('student_id')

        if student_id is None:
            return redirect('/manage_student')

        form = EditStudentForm(request.POST, request.FILES)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            address = form.cleaned_data['address']
     
            preferred_category = form.cleaned_data['preferred_category']
            gender = form.cleaned_data['gender']
            grade = form.cleaned_data['grade']  
            code_PPR = form.cleaned_data['code_PPR']
            reference = form.cleaned_data['reference']
            
            # Getting Profile Pic first
            if len(request.FILES) != 0:
                profile_pic = request.FILES['profile_pic']
                fs = FileSystemStorage()
                filename = fs.save(profile_pic.name, profile_pic)
                profile_pic_url = fs.url(filename)
            else:
                profile_pic_url = None

            try:
                # First Update into Custom User Model
                user = CustomUser.objects.get(id=student_id)
                user.first_name = first_name
                user.last_name = last_name
                user.username = username
                user.email = email
                user.save()

                # Then Update Students Table
                student = Students.objects.get(admin=student_id)
                student.address = address
              
                student.preferred_category = preferred_category
                student.gender = gender
                student.grade = grade  
                student.code_PPR = code_PPR 
                student.reference = reference  

                if profile_pic_url is not None:
                    student.profile_pic = profile_pic_url
                student.save()

                del request.session['student_id']
                messages.success(request, "Student Updated Successfully!")
                return redirect('/edit_student/' + str(student_id))
            except Exception as e:
                messages.error(request, f"Failed to Update Student: {str(e)}")
                return redirect('/edit_student/' + str(student_id))
        else:
            return redirect('/edit_student/' + str(student_id))



def delete_student(request, student_id):
    students = Students.objects.filter(admin=student_id)
    
    if students.exists():
        # Delete all matching students
        students.delete()
        messages.success(request, "Student(s) Deleted Successfully.")
    else:
        messages.error(request, "No Student found to delete.")
        
    return redirect('manage_student')


@csrf_exempt
def check_email_exist(request):
    email = request.POST.get("email")
    user_obj = CustomUser.objects.filter(email=email).exists()
    if user_obj:
        return HttpResponse(True)
    else:
        return HttpResponse(False)



@csrf_exempt
def check_username_exist(request):
    username = request.POST.get("username")
    user_obj = CustomUser.objects.filter(username=username).exists()
    if user_obj:
        return HttpResponse(True)
    else:
        return HttpResponse(False)



@csrf_exempt
def check_code_PPR_exist(request):
    if request.method == "POST":
        code_PPR = request.POST.get("code_PPR")
        student_obj = Students.objects.filter(code_PPR=code_PPR).exists()
        if student_obj:
            return HttpResponse("True")
        else:
            return HttpResponse("False")
    return HttpResponse("Method Not Allowed", status=405)



def admin_view_attendance(request):
    try:
        courses = Courses.objects.all()
        students = Students.objects.all()
        context = {
            "courses": courses,
            "students": students
        }
        return render(request, "hod_template/admin_view_attendance.html", context)
    except Exception as e:
        print(f"Error: {e}")
        return render(request, "hod_template/error.html", {"error": str(e)})



def admin_get_attendance_courses(request):
    # Ensure the request method is POST
    if request.method == 'POST':
        course_id = request.POST.get('course')
        
        if course_id:
            try:
                # Fetch the course and attendance data
                course = Courses.objects.get(id=course_id)
                attendance = Attendance.objects.filter(course_id=course_id)
                
                # Prepare the context for rendering the template
                context = {
                    "course": course,
                    "attendance": attendance
                }
                
                # Render the template with the context
                html = render_to_string('hod_template/partials/attendance_by_course.html', context, request=request)
                return JsonResponse({'html': html})
            
            except Courses.DoesNotExist:
                # Handle the case where the course does not exist
                return JsonResponse({'error': 'Course not found'}, status=404)
        
        return JsonResponse({'error': 'No course ID provided'}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)



def admin_get_group_students(request):
    if request.method == 'POST':
        group_id = request.POST.get('group')
        
        if group_id:
            try:
                # Fetch the group and students data
                group = Group.objects.get(id=group_id)
                students = Students.objects.filter(group=group)
                
                # Fetch attendance records for the group
                attendances = Attendance.objects.filter(group=group)
                
                # Fetch attendance reports for the students
                attendance_reports = AttendanceReport.objects.filter(
                    student_id__in=students.values_list('id', flat=True),
                    attendance_id__in=attendances
                )

                # Prepare context for rendering the template
                context = {
                    "group": group,
                    "students": students,
                    "attendance_reports": attendance_reports
                }
                
                # Render the template with the context
                html = render_to_string('hod_template/partials/attendance_report.html', context, request=request)
                return JsonResponse({'html': html})
            
            except Group.DoesNotExist:
                return JsonResponse({'error': 'Group not found'}, status=404)
        
        return JsonResponse({'error': 'No group ID provided'}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)



def admin_profile(request):
    user = CustomUser.objects.get(id=request.user.id)
    context={
        "user": user
    }
    return render(request, 'hod_template/admin_profile.html', context)



def admin_profile_update(request):
    if request.method != "POST":
        messages.error(request, "Invalid Method!")
        return redirect('admin_profile')
    else:
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')

        try:
            customuser = CustomUser.objects.get(id=request.user.id)
            customuser.first_name = first_name
            customuser.last_name = last_name
            if password != None and password != "":
                customuser.set_password(password)
            customuser.save()
            messages.success(request, "Profile Updated Successfully")
            return redirect('admin_profile')
        except:
            messages.error(request, "Failed to Update Profile")
            return redirect('admin_profile')






@transaction.atomic
def manage_groups(request):
    min_group_size = 8
    max_group_size = 14

    if request.method == "POST":
        avoid_days = request.POST.getlist('avoid_days', [])
        create_days = request.POST.getlist('create_days', [])
        max_salle_disponible = int(request.POST.get('max_salle_disponible', 0))

        if not create_days:
            create_days = [day.name for day in Day.objects.all()]

        categories = ['Morning', 'Evening']
        all_groups = []

        try:
            while True:
                total_students = Students.objects.filter(group__isnull=True).count()
                if total_students == 0:
                    break  # No students left to group, exit the loop

                available_courses = list(Courses.objects.all())
                if not available_courses:
                    messages.error(request, "No courses available for scheduling.")
                    return render(request, 'hod_template/manage_groups_template.html', {'form': GroupingForm()})

                random.shuffle(available_courses)
                course_index = 0

                used_courses = set()
                group_used_courses = {}

                for category in categories:
                    all_students = list(Students.objects.filter(group__isnull=True, preferred_category=category))
                    random.shuffle(all_students)

                    groups = []
                    while all_students and len(groups) < max_salle_disponible:
                        new_group = []
                        while len(new_group) < max_group_size and all_students:
                            new_group.append(all_students.pop(0))
                        groups.append(new_group)

                    for group_students in groups[:]:
                        if len(group_students) < min_group_size:
                            added = False
                            for student in group_students:
                                for larger_group in groups:
                                    if larger_group is not group_students and len(larger_group) < max_group_size:
                                        larger_group.append(student)
                                        added = True
                                        break
                            if added:
                                groups.remove(group_students)

                    for group_students in groups:
                        if group_students:
                            new_group = Group.objects.create(category=category)
                            group_used_courses[new_group.id] = set()
                            days_assigned = set()

                            for day_name in create_days:
                                if course_index >= len(available_courses):
                                    break  # Stop if no more courses are available

                                assigned_course = available_courses[course_index]

                                if (assigned_course.id in used_courses or
                                    assigned_course.id in group_used_courses[new_group.id]):
                                    continue

                                day, _ = Day.objects.get_or_create(name=day_name)
                                if day in days_assigned:
                                    continue  # Avoid assigning the same day twice

                                # Schedule the courses for the day with non-overlapping times
                                times = []
                                if category == 'Morning':
                                    times = [('08:30', '10:30'), ('10:45', '12:30')]
                                else:
                                    times = [('13:30', '15:00'), ('15:15', '16:30')]

                                for start_time, end_time in times:
                                    if assigned_course.id not in group_used_courses[new_group.id]:
                                        new_group.courses.add(assigned_course)
                                        new_group.days_of_week.add(day)
                                        new_group.create_initial_schedule()
                                        days_assigned.add(day)
                                        group_used_courses[new_group.id].add(assigned_course.id)
                                        used_courses.add(assigned_course.id)

                                        new_group.save()
                                        course_index += 1
                                        if course_index >= len(available_courses):
                                            break  # Stop if no more courses are available

                            for student in group_students:
                                student.group = new_group
                                student.save()

                    all_groups.extend(groups)

                    if course_index >= len(available_courses):
                        break  # Stop creating groups if all courses are scheduled

            no_preference_students = list(Students.objects.filter(group__isnull=True, preferred_category__isnull=True))
            random.shuffle(no_preference_students)

            for student in no_preference_students:
                for group in all_groups:
                    if len(group) < max_group_size:
                        student.group = group
                        student.save()
                        break

            for day_name in avoid_days:
                day = Day.objects.filter(name=day_name).first()
                if day:
                    groups_to_check = Group.objects.filter(days_of_week=day)
                    for group in groups_to_check:
                        group.days_of_week.remove(day)
                        if not group.days_of_week.exists() or not group.students.exists():
                            group.delete()

            Group.objects.annotate(students_count=Count('students')).filter(students_count=0).delete()

            messages.success(request, "Groups have been successfully managed and assigned to students.")
        except IntegrityError as e:
            transaction.set_rollback(True)
            messages.error(request, f"An error occurred while managing groups: {e}")
            return render(request, 'hod_template/manage_groups_template.html', {'form': GroupingForm()})

        groups = Group.objects.all().annotate(students_count=Count('students'))

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('hod_template/group_list_partial.html', {'course_groups': groups}, request=request)
            return JsonResponse({'group_list_html': html})
        else:
            print("Not an AJAX request")

    groups = Group.objects.all().annotate(students_count=Count('students'))
    groups_count = Group.objects.all().count()
    context = {
        "course_groups": groups,
        "groups_count" : groups_count,
        "form": GroupingForm(),
    }
    return render(request, 'hod_template/manage_groups_template.html', context)






def group_detail(request, group_id):
    group = Group.objects.get(id=group_id)
    students = Students.objects.filter(group=group)
    context = {
        'group': group,
        'students': students,
    }
    return render(request, 'hod_template/group_detail.html', context)


def add_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.save()

            # Handle many-to-many relationships
            days_of_week = form.cleaned_data.get('days_of_week')
            group.days_of_week.set(days_of_week)  # Set the selected days of the week

            all_courses = Courses.objects.all()
            group.courses.set(all_courses)  # Assign all courses to the group

            # Add success message
            messages.success(request, 'Group successfully created!')

            return redirect('manage_groups')  # Ensure this URL name is correct
        else:
            # Print form errors for debugging
            print(form.errors)
            print('Form is not valid.')
    else:
        form = GroupForm()

    context = {
        'form': form,
    }
    return render(request, 'hod_template/add_group_template.html', context)


def delete_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    
    if request.method == 'POST':
        group.delete()

        # Add success message
        messages.success(request, 'Group successfully deleted!')
        
        return redirect('manage_groups')  # Redirect to a page that lists the groups

    # If it's not a POST request, redirect to a safe page
    return redirect('manage_groups')



def manage_staff_groups(request):
    staff_members = Staffs.objects.select_related('admin', 'course').all()
    groups = Group.objects.all()
    
    # Create a list of dictionaries with staff ID and their assigned group IDs
    staff_groups = [
        {
            'staff_id': staff.id,
            'assigned_group_ids': list(staff.groups.values_list('id', flat=True))
        }
        for staff in staff_members
    ]

    context = {
        'staff_members': staff_members,
        'groups': groups,
        'staff_groups': staff_groups,
    }
    return render(request, 'hod_template/manage_staff_groups.html', context)





def manage_student_groups(request):
    students = Students.objects.all()
    groups = Group.objects.all()
    
    # Assuming Day model is defined and you have instances of days of the week
    categories = [choice[0] for choice in Group.CATEGORY_CHOICES]

    context = {
        'students': students,
        'groups': groups,
        'categories': categories,
    }
    return render(request, 'hod_template/manage_student_groups.html', context)




def update_staff_group(request):
    if request.method == "POST":
        group_ids = request.POST.getlist('group')  # Handle multiple groups
        staff_id = request.POST.get('staff_id')

        try:
            staff = Staffs.objects.get(id=staff_id)

            # Debugging: Print received group_ids and staff_id
            print(f"Received group_ids: {group_ids}, staff_id: {staff_id}")

            if group_ids:
                # Ensure group_ids is not empty and filter groups
                groups = Group.objects.filter(id__in=group_ids)

                if groups.exists():
                    staff.groups.set(groups)  # Set multiple groups
                else:
                    messages.error(request, "Selected groups not found")
                    return redirect('manage_staff_groups')
            else:
                staff.groups.clear()  # Clear groups if no groups are selected

            # Debugging: Print staff details after assigning new groups
            print(f"Assigned Groups - Staff: {staff.id}, New Groups: {list(staff.groups.all().values_list('id', flat=True))}")

            staff.save()

            messages.success(request, "Staff groups updated successfully")
        except Staffs.DoesNotExist:
            messages.error(request, "Staff not found")
        except Group.DoesNotExist:
            messages.error(request, "One or more groups not found")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            print(f"Exception occurred: {str(e)}")

    return redirect('manage_staff_groups')





def update_student_group(request):
    if request.method == "POST":
        group_id = request.POST.get('group')  # Handle a single group
        student_id = request.POST.get('student_id')

        try:
            student = Students.objects.get(id=student_id)

            if group_id:
                group = Group.objects.get(id=group_id)
                student.group = group  # Set the group for the student
            else:
                student.group = None  # Clear the group if no group is selected

            student.save()


            messages.success(request, "Student group updated successfully")
        except Students.DoesNotExist:
            messages.error(request, "Student not found")
        except Group.DoesNotExist:
            messages.error(request, "Selected group not found")

    return redirect('manage_student_groups')



def staff_profile(request):
    pass


def student_profile(requtest):
    pass



def generate_certificate_view(request, project_id):
    # Fetch the project or return a 404 error if not found
    project = get_object_or_404(Project, id=project_id)

    # Fetch the student related to the project
    student = get_object_or_404(Students, id=project.student.id)
    
    # Ensure the encadrant is set and has the necessary attributes
    if project.encadrant and hasattr(project.encadrant.admin, 'first_name') and hasattr(project.encadrant.admin, 'last_name'):
        trainer_name = f"{project.encadrant.admin.last_name}, {project.encadrant.admin.first_name}"
    else:
        trainer_name = "N/A"  # Or handle it as needed if trainer details are missing
    
    # Generate certificate for the project
    buffer = generate_certificate(
        student_name=f'{student.admin.last_name} {student.admin.first_name}',  # Assuming a method to get full name
        ppr=student.code_PPR,
        reference=student.reference,
        project_title=project.title,
        trainer_name=trainer_name
    )
    
    # Return the certificate as a downloadable PDF
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificate_{project_id}.pdf"'
    
    return response



def print_certificate_template(request):
    # Fetch full project objects
    projects = Project.objects.all()
    print(projects)  # Debug print statement
    return render(request, 'hod_template/print_certificate_template.html', {'projects': projects})


def manage_timetable(request):
    groups = Group.objects.all()  # Assuming you have a Group model
    return render(request, 'hod_template/manage_timetable.html', {'groups': groups})


def group_timetable(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    timetable = GroupSchedule.objects.filter(group=group).order_by('day_of_week', 'start_time')
    
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('start_time_'):
                schedule_id = key.split('_')[2]
                schedule = get_object_or_404(GroupSchedule, id=schedule_id)
                start_time = request.POST.get(f'start_time_{schedule_id}')
                end_time = request.POST.get(f'end_time_{schedule_id}')
                category = request.POST.get(f'category_{schedule_id}')
                schedule.start_time = start_time
                schedule.end_time = end_time
                schedule.category = category
                schedule.save()
        return redirect(reverse('group_timetable', args=[group.id]))
    
    return render(request, 'hod_template/group_timetable.html', {'timetable': timetable, 'selected_group': group})


def delete_schedule(request, schedule_id):
    # Retrieve the schedule object or raise 404 if not found
    schedule = get_object_or_404(GroupSchedule, id=schedule_id)
    
    # Perform the deletion
    schedule.delete()
    
    # Redirect to the manage timetable page
    return redirect('manage_timetable')



def delete_students_with_excessive_absences(request):
    MAX_ALLOWED_ABSENCES = 3
    
    students = Students.objects.all()
    
    for student in students:
        absences_count = AttendanceReport.objects.filter(student_id=student, status=True).count()
        
        if absences_count > MAX_ALLOWED_ABSENCES:
            # Add student to blacklist
            BlacklistedStudent.objects.create(
                student=student.admin,  # Assuming `admin` is a User instance related to the student
                reason="Exceeded maximum allowed absences"
            )
            
            # Delete the student
            student.delete()
            messages.info(request, f"Student {student.admin.username} has been deleted and blacklisted due to excessive absences.")
    
    return redirect('admin_view_attendance')






