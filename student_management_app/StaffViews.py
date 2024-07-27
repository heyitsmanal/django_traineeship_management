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

from student_management_app.models import  CustomUser, Group, Note, Project, Staffs, Courses, Students, Attendance, AttendanceReport, StudentResult


def staff_home(request):
    try:
        # Fetching the staff member
        staff = Staffs.objects.get(admin=request.user)

        # Fetching All Courses under Staff
        courses = Courses.objects.filter(staffs__admin=request.user)
        course_count = courses.count()
        course_ids = courses.values_list('id', flat=True)
        
        # Total Students in Courses
        students_count = Students.objects.filter(courses__in=course_ids).count()

        # Fetch All Attendance Count
        attendance_count = Attendance.objects.filter(course__in=course_ids).count()  # Fixed the lookup to use 'course'

        # Fetch Attendance Data by Courses
        course_list = []
        attendance_list = []
        for course in courses:
            attendance_count1 = Attendance.objects.filter(course=course).count()
            course_list.append(course.course_name)
            attendance_list.append(attendance_count1)

        students_attendance = Students.objects.filter(courses__in=course_ids)  # Updated filter to use 'courses'
        student_list = []
        student_list_attendance_present = []
        student_list_attendance_absent = []
        for student in students_attendance:
            attendance_present_count = AttendanceReport.objects.filter(status=True, student_id=student).count()
            attendance_absent_count = AttendanceReport.objects.filter(status=False, student_id=student).count()
            student_list.append(f"{student.admin.first_name} {student.admin.last_name}")
            student_list_attendance_present.append(attendance_present_count)
            student_list_attendance_absent.append(attendance_absent_count)

        context = {
            "students_count": students_count,
            "attendance_count": attendance_count,
            "course_list": course_list,
            "attendance_list": attendance_list,
            "student_list": student_list,
            "attendance_present_list": student_list_attendance_present,
            "attendance_absent_list": student_list_attendance_absent,
            "course_count": course_count
        }
        return render(request, "staff_template/staff_home_template.html", context)
    except Staffs.DoesNotExist:
        messages.error(request, "Staff not found.")
        return redirect('doLogin')






def get_courses():
    return Courses.objects.all()

def get_groups(staff_id=None, day_of_week=None):
    if staff_id and day_of_week:
        return Group.objects.filter(staffs__id=staff_id, day_of_week=day_of_week)
    elif staff_id:
        return Group.objects.filter(staffs__id=staff_id)
    elif day_of_week:
        return Group.objects.filter(day_of_week=day_of_week)
    return Group.objects.all()

def get_students_by_group(group_id):
    group = get_object_or_404(Group, id=group_id)
    return Students.objects.filter(group=group)

def get_attendances(course_id, day_of_week, category):
    return Attendance.objects.filter(course_id=course_id, day_of_week=day_of_week, category=category).values('id', 'attendance_date')

def handle_error(e, message="An error occurred"):
    print(f"Error: {e}")
    return JsonResponse({'error': message}, status=500)

def select_course_group(request):
    courses = get_courses()
    groups = get_groups()
    return render(request, 'staff_template/manage_attendance_template.html', {'courses': courses, 'groups': groups})

def list_attendances(request, course_id, day_of_week, category):
    try:
        attendances = get_attendances(course_id, day_of_week, category)
        students_exist = Students.objects.filter(course_id=course_id, day_of_week=day_of_week, category=category).exists()

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

def get_groups_view(request, course_id):
    try:
        day_of_week = request.GET.get('day_of_week', '')
        groups = get_groups(course_id, day_of_week)
        response_data = {'groups': list(groups.values('day_of_week', 'category'))}
        return JsonResponse(response_data)
    except Exception as e:
        return handle_error(e, 'An error occurred while fetching groups. Please try again.')




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
            # Fetch the group and associated course
            group = get_object_or_404(Group, id=int(group_id))
            course = group.course
            
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
                    status=True  # Mark student as absent
                )
            
            messages.success(request, "Attendance saved successfully.")
            return JsonResponse({"status": "success", "message": "Attendance saved successfully"})
        
        except Exception as e:
            print(f"Error occurred: {e}")  # Print the exception for debugging
            messages.error(request, "An error occurred while saving attendance.")
            return JsonResponse({"status": "failed", "message": "Error occurred"}, status=500)
    
    messages.error(request, "Method not allowed.")
    return JsonResponse({"status": "failed", "message": "Method not allowed"}, status=405)



def staff_update_attendance(request):
    try:
        staff = Staffs.objects.get(admin=request.user)
        courses = Courses.objects.filter(staffs__admin=request.user)
        return render(request, "staff_template/update_attendance_template.html", {"courses": courses})
    except Staffs.DoesNotExist:
        messages.error(request, "Staff not found.")
        return redirect('some_error_page')



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
        print(f"Staff ID: {staff_id}")

        groups = get_groups(staff_id=staff_id)
        print(f"Groups found: {groups.count()}")

        context = {
            'groups': groups,
            'course_name': staff.course.course_name  
        }
        return render(request, "staff_template/add_note_template.html", context)
        
    except Staffs.DoesNotExist:
        messages.error(request, "Staff not found.")
        return redirect('some_error_page')







@csrf_exempt
def save_notes_data(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=400)
    
    try:
        group_id = request.POST.get('group_id')
        notes_date = request.POST.get('notes_date')
        
        # Separate the notes for assignment and exam
        assignment_notes_dict = {key: value for key, value in request.POST.items() if key.startswith('assignment_notes[')}
        exam_notes_dict = {key: value for key, value in request.POST.items() if key.startswith('exam_notes[')}
        
        group = get_object_or_404(Group, id=group_id)
        course = group.course

        for note_key, note_value in assignment_notes_dict.items():
            student_id = note_key.split('[')[1].split(']')[0]
            
            try:
                student = get_object_or_404(Students, id=student_id)
                
                # Create or update the Note object for assignment
                Note.objects.update_or_create(
                    student=student,
                    course=course,
                    note_type='A',  # 'A' for Assignment
                    defaults={'content': note_value, 'note_date': notes_date}
                )

            except IndexError:
                messages.error(f"Error processing assignment note_key: {note_key}")
                return JsonResponse({"error": "Invalid note key format"}, status=400)
            except Exception as e:
                print(f"An error occurred while saving assignment note for student {student_id}: {str(e)}")

        for note_key, note_value in exam_notes_dict.items():
            student_id = note_key.split('[')[1].split(']')[0]
            
            try:
                student = get_object_or_404(Students, id=student_id)
                
                # Create or update the Note object for exam
                Note.objects.update_or_create(
                    student=student,
                    course=course,
                    note_type='E',  # 'E' for Exam
                    defaults={'content': note_value, 'note_date': notes_date}
                )

            except IndexError:
                messages.error(f"Error processing exam note_key: {note_key}")
                return JsonResponse({"error": "Invalid note key format"}, status=400)
            except Exception as e:
                print(f"An error occurred while saving exam note for student {student_id}: {str(e)}")

        return JsonResponse({"success": "Notes saved successfully"})

    except Group.DoesNotExist:
        return JsonResponse({"error": f"Group with id {group_id} does not exist"}, status=404)
    except Exception as e:
        messages.error(f"An error occurred: {str(e)}")
        return JsonResponse({"error": "Failed to save notes"}, status=500)

        




































def validate_project(request):
    search_term = request.GET.get('search', '')
    filter_by = request.GET.get('filter_by', 'projects')
    
    # Initialize empty lists for projects and students
    projects = Project.objects.all()
    students = Students.objects.all()
    
    results_found = True
    
    if search_term:
        if filter_by == 'students':
            filtered_students = Students.objects.filter(
                Q(first_name__icontains=search_term) | Q(last_name__icontains=search_term)
            )
            if not filtered_students.exists():
                results_found = False
            # Filter projects by the filtered students
            projects = projects.filter(student__in=filtered_students)
        elif filter_by == 'projects':
            projects = projects.filter(title__icontains=search_term)
            if not projects.exists():
                results_found = False

    return render(
        request, 
        'staff_template/validate_projects.html', 
        {
            'form': ProjectValidationForm(), 
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