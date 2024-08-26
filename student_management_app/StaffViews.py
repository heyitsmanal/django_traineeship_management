from datetime import datetime
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.core.files.storage import FileSystemStorage #To upload Profile Picture
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Q 

from django.contrib.auth.decorators import login_required

from student_management_app.forms import ProjectValidationForm

from student_management_app.models import  CustomUser, Day, Group, GroupSchedule, Note, Project, Staffs, Courses, Students, Attendance, AttendanceReport, StudentResult

def staff_home(request):
    try:
        # Fetching the staff member
        staff = Staffs.objects.get(admin=request.user)

        # Fetching all courses under the staff
        courses = Courses.objects.filter(staffs__admin=request.user)
        course_count = courses.count()
        course_ids = courses.values_list('id', flat=True)
        
        # Total students in courses
        students_count = Students.objects.filter(courses__in=course_ids).count()

        # Fetch all attendance count
        attendance_count = Attendance.objects.filter(course__in=course_ids).count()

        # Fetch attendance data by courses
        course_list = []
        attendance_list = []
        for course in courses:
            attendance_count1 = Attendance.objects.filter(course=course).count()
            course_list.append(course.course_name)
            attendance_list.append(attendance_count1)

        # Fetch students' attendance
        students_attendance = Students.objects.filter(courses__in=course_ids)
        student_list = []
        student_list_attendance_present = []
        student_list_attendance_absent = []
        for student in students_attendance:
            attendance_present_count = AttendanceReport.objects.filter(status=True, student_id=student).count()
            attendance_absent_count = AttendanceReport.objects.filter(status=False, student_id=student).count()
            student_list.append(f"{student.admin.first_name} {student.admin.last_name}")
            student_list_attendance_present.append(attendance_present_count)
            student_list_attendance_absent.append(attendance_absent_count)

        # Fetching group schedules and separating by session
        morning_groups = GroupSchedule.objects.filter(course__in=course_ids, category='morning')
        evening_groups = GroupSchedule.objects.filter(course__in=course_ids, category='evening')

        context = {
            "students_count": students_count,
            "attendance_count": attendance_count,
            "course_list": course_list,
            "attendance_list": attendance_list,
            "student_list": student_list,
            "attendance_present_list": student_list_attendance_present,
            "attendance_absent_list": student_list_attendance_absent,
            "course_count": course_count,
            "morning_groups": morning_groups,
            "evening_groups": evening_groups,
        }
        return render(request, "staff_template/staff_home_template.html", context)
    except Staffs.DoesNotExist:
        messages.error(request, "Staff not found.")
        return redirect('doLogin')


def get_courses():
    return Courses.objects.all()

def get_groups(staff_id=None, day_of_week=None):
    if staff_id and day_of_week:
        return Group.objects.filter(staffs__id=staff_id, days_of_week__name=day_of_week)
    elif staff_id:
        return Group.objects.filter(staffs__id=staff_id)
    elif day_of_week:
        return Group.objects.filter(days_of_week__name=day_of_week)
    return Group.objects.all()

def get_students_by_group(group_id):
    group = get_object_or_404(Group, id=group_id)
    return Students.objects.filter(group=group)


def get_attendances(course_id, day_name, category):
    # Find the corresponding Day object
    try:
        day = Day.objects.get(name=day_name)
    except Day.DoesNotExist:
        return Attendance.objects.none()  # Return an empty queryset if the day doesn't exist

    return Attendance.objects.filter(course_id=course_id, group__days_of_week=day, group__category=category).values('id', 'attendance_date')


def handle_error(e, message="An error occurred"):
    print(f"Error: {e}")
    return JsonResponse({'error': message}, status=500)



def list_attendances(request, course_id, day_name, category):
    try:
        # Find the corresponding Day object
        try:
            day = Day.objects.get(name=day_name)
        except Day.DoesNotExist:
            return JsonResponse({'error': 'Invalid day selected.', 'attendances': []})

        # Fetch attendances using the modified get_attendances function
        attendances = get_attendances(course_id, day_name, category)

        # Check if any students exist for the specified course, day, and category
        students_exist = Students.objects.filter(
            course_id=course_id,
            group__days_of_week=day,
            group__category=category
        ).exists()

        if not students_exist:
            return JsonResponse({'error': 'No students found for the selected group.', 'attendances': []})

        return JsonResponse({'attendances': list(attendances)})
    except Exception as e:
        return handle_error(e, 'An error occurred while fetching attendances. Please try again.')

def view_attendance(request, attendance_id):
    try:
        attendance = get_object_or_404(Attendance, id=attendance_id)
        students = Students.objects.filter(attendance=attendance)
        student_data = [{'first_name': student.first_name, 'last_name': student.last_name, 'presence': student.presence} for student in students]
        return JsonResponse({'attendance_date': attendance.attendance_date.strftime('%Y-%m-%d'), 'students': student_data})
    except Exception as e:
        return handle_error(e, 'An error occurred while fetching attendance details. Please try again.')


def staff_take_attendance(request):
    staff = Staffs.objects.get(admin=request.user.id)
    # Get all courses the staff member is associated with
    course = staff.course
    groups = Group.objects.all()
    context = {
        'course' : course,
        'groups': groups, 
        'course_name': course.course_name
    }
    return render(request, 'staff_template/take_attendance_template.html', context)


@csrf_exempt
def save_attendance_data(request):
    if request.method == 'POST':
        student_ids = request.POST.getlist("student_ids[]")
        group_id = request.POST.get("group_id")
        attendance_date = request.POST.get("attendance_date")
        
        if not group_id:
            messages.error(request, "Group ID is missing.")
            return JsonResponse({"status": "failed", "message": "group_id is missing"}, status=400)

        if not attendance_date:
            messages.error(request, "Attendance date is missing.")
            return JsonResponse({"status": "failed", "message": "attendance_date is missing"}, status=400)

        try:
            # Fetch the group
            group = get_object_or_404(Group, id=int(group_id))
            
            # Retrieve all associated courses
            courses = group.courses.all()
            
            if not courses.exists():
                messages.error(request, "No courses found for the group.")
                return JsonResponse({"status": "failed", "message": "No courses found for the group"}, status=404)
            
            # For simplicity, assume the group is associated with a single course. If there are multiple, handle as needed.
            course = courses.first()
            
            # Create or get the Attendance object
            attendance, created = Attendance.objects.get_or_create(
                course=course, 
                attendance_date=datetime.strptime(attendance_date, '%Y-%m-%d').date(), 
                group=group
            )
            
            # Debugging information
            print(f"Attendance object created: {attendance}")
            
            # Remove existing AttendanceReport entries for the same course and date
            AttendanceReport.objects.filter(
                attendance_id=attendance,
                student_id__in=student_ids
            ).delete()
            
            # Create new AttendanceReport entries for each student
            for student_id in student_ids:
                student = get_object_or_404(Students, id=int(student_id))
                
                # Debugging information
                print(f"Creating AttendanceReport for student: {student} in course: {course}")
                
                # Create AttendanceReport for each student
                AttendanceReport.objects.create(
                    student_id=student, 
                    attendance_id=attendance, 
                    status=True  # Mark student as present
                )
                
                # Check for absences and expel if necessary
                absences = AttendanceReport.objects.filter(student_id=student, status=False).count()
                if absences >= 4:
                    student.blacklisted = True
                    student.save()
                    print(f"Student {student.id} has been expelled for excessive absences.")

            messages.success(request, "Attendance saved successfully.")
            return JsonResponse({"status": "success", "message": "Attendance saved successfully"})
        
        except Exception as e:
            print(f"Error occurred: {e}")  # Print the exception for debugging
            messages.error(request, "An error occurred while saving attendance.")
            return JsonResponse({"status": "failed", "message": "Error occurred"}, status=500)
    
    messages.error(request, "Method not allowed.")
    return JsonResponse({"status": "failed", "message": "Method not allowed"}, status=405)





def get_students(request, groupid):
    students = get_students_by_group(groupid)
    list_data = [{"id": student.id, "name": student.admin.get_full_name()} for student in students]
    return JsonResponse(list_data, safe=False)


def staff_profile(request):
    user = CustomUser.objects.get(id=request.user.id)
    staff = Staffs.objects.get(admin=user)

    context={
        "user": user,
        "staff": staff
    }
    return render(request, 'staff_template/staff_profile.html', context)



def staff_profile_update(request):
    if request.method != "POST":
        messages.error(request, "Invalid Method!")
        return redirect('staff_profile')
    else:
        profile_pic = request.POST.get('profile_pic')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        address = request.POST.get('address')

        try:
            customuser = CustomUser.objects.get(id=request.user.id)
            customuser.first_name = first_name
            customuser.last_name = last_name
            if password != None and password != "":
                customuser.set_password(password)
            customuser.save()

            staff = Staffs.objects.get(admin=customuser.id)
            staff.profile_pic = profile_pic
            staff.address = address
            staff.save()

            messages.success(request, "Profile Updated Successfully")
            return redirect('staff_profile')
        except:
            messages.error(request, "Failed to Update Profile")
            return redirect('staff_profile')



def staff_add_note(request):
    try:
        staff = get_object_or_404(Staffs, admin=request.user)
       
        staff_id = staff.id
        staff = get_object_or_404(Staffs, id=staff_id)

        groups = staff.groups.all()
        print(f"Staff ID: {staff.id}")
        print(f"Groups found: {groups.count()}")

        context = {
            'groups': groups,
            'course_name': staff.course.course_name if staff.course else 'No Course Assigned'
        }
        return render(request, "staff_template/add_note_template.html", context)
        
    except Staffs.DoesNotExist:
        messages.error(request, "Staff not found.")
        return render(request, "404.html")  # Ensure to render the correct 404 template
    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return render(request, "404.html") 




@csrf_exempt
def save_notes_data(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=400)
    
    group_id = request.POST.get('group_id')
    notes_date = request.POST.get('notes_date')
    
    if not group_id or not notes_date:
        return JsonResponse({"error": "Missing required parameters"}, status=400)
    
    try:
        group = get_object_or_404(Group, id=group_id)
        staff = get_object_or_404(Staffs, admin=request.user)
        staff_course = staff.course
        
        if not staff_course:
            return JsonResponse({"error": "Staff does not have an assigned course"}, status=400)

        if staff_course not in group.courses.all():
            return JsonResponse({"error": "The group does not have the staff's course"}, status=400)

        assignment_notes_dict = {key: value for key, value in request.POST.items() if key.startswith('assignment_notes[')}
        exam_notes_dict = {key: value for key, value in request.POST.items() if key.startswith('exam_notes[')}

        def process_notes(note_dict, note_type):
            for note_key, note_value in note_dict.items():
                try:
                    student_id = note_key.split('[')[1].split(']')[0]
                    student = get_object_or_404(Students, id=student_id)
                    
                    Note.objects.update_or_create(
                        student=student,
                        course=staff_course,
                        note_type=note_type,
                        defaults={'content': note_value, 'note_date': notes_date}
                    )
                except IndexError:
                    return JsonResponse({"error": "Invalid note key format"}, status=400)
                except Exception as e:
                    return JsonResponse({"error": f"Failed to save {note_type} note"}, status=500)

        process_notes(assignment_notes_dict, 'A')  # 'A' for Assignment
        process_notes(exam_notes_dict, 'E')        # 'E' for Exam

        return JsonResponse({"success": "Notes saved successfully", "message": "Notes saved successfully"})

    except Group.DoesNotExist:
        return JsonResponse({"error": f"Group with id {group_id} does not exist"}, status=404)
    except Staffs.DoesNotExist:
        return JsonResponse({"error": "Staff not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": "Failed to save notes"}, status=500)




def validate_project(request):
    search_term = request.GET.get('search', '')
    filter_by = request.GET.get('filter_by', 'projects')
    projects = Project.objects.all()
    students = Students.objects.all()
    results_found = True

    if request.method == 'POST':
        form = ProjectValidationForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            staff = get_object_or_404(Staffs, admin=request.user)

            # Check if the student already has a project
            if Project.objects.filter(student=project.student).exists():
                messages.error(request, 'This student already has a project.')
                return redirect('validate_project')

            project.encadrant = staff
            project.save()
            messages.success(request, 'Project validated successfully.')
            return redirect('validate_project')
    else:
        form = ProjectValidationForm()

    if search_term:
        if filter_by == 'students':
            filtered_students = Students.objects.filter(
                Q(first_name__icontains=search_term) | Q(last_name__icontains=search_term)
            )
            if filtered_students.exists():
                projects = projects.filter(student__in=filtered_students)
            else:
                results_found = False
        elif filter_by == 'projects':
            projects = projects.filter(title__icontains=search_term)
            if not projects.exists():
                results_found = False

    return render(
        request, 
        'staff_template/validate_projects.html', 
        {
            'form': form, 
            'projects': projects, 
            'students': students,
            'search_term': search_term, 
            'filter_by': filter_by,
            'results_found': results_found
        }
    )




def delete_project(request, project_id):
    if request.method == 'GET':
        project = get_object_or_404(Project, id=project_id)
        project.delete()
        messages.success(request, "Project deleted successfully.")
        return redirect('validate_project')  # Redirect to the page with the form and table
    else:
        messages.error(request, "Invalid request method.")
        return redirect('validate_project')  # Handle other methods if necessary