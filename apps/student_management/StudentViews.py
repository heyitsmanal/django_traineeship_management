from io import BytesIO
from venv import logger
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseRedirect, FileResponse
from django.contrib import messages
from django.core.files.storage import FileSystemStorage  # To upload Profile Picture
from django.urls import reverse
from django.core.files import File
from django.contrib.auth.decorators import login_required
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4   
from django.contrib.staticfiles import finders
from PyPDF2 import PdfReader, PdfWriter

from apps.student_management.models import Certificat, CustomUser, Group, GroupSchedule, Note, NoteType, Project, Staffs, Courses, StudentResult, Students, Attendance, AttendanceReport
from apps.student_management.utils import generate_certificate


def student_home(request):
    try:
        student_obj = Students.objects.get(admin=request.user)
        total_attendance = AttendanceReport.objects.filter(student_id=student_obj.id).count()
        attendance_present = AttendanceReport.objects.filter(student_id=student_obj.id, status=True).count()
        attendance_absent = AttendanceReport.objects.filter(student_id=student_obj.id, status=False).count()
        courses = student_obj.courses.all()
        total_attendance_by_course = sum(Attendance.objects.filter(course=course).count() for course in courses)
        project = Project.objects.filter(student=student_obj).first()

        student_group = student_obj.group
        if student_group:
            timetable = GroupSchedule.objects.filter(group=student_group).order_by('day_of_week__name', 'start_time')
            days_of_week = ' - '.join(day.name for day in student_group.days_of_week.all())  # Fetch names of days
        else:
            timetable = []
            days_of_week = []

        context = {
            'student_group_day_of_week': days_of_week if student_group else "No Group",
            'student_group_category': student_group.category if student_group else "No Group",
            'project': project,
            "total_attendance": total_attendance,
            "attendance_present": attendance_present,
            "attendance_absent": attendance_absent,
            "total_attendance_by_course": total_attendance_by_course,
            'timetable': timetable,
        }
        return render(request, "student_template/student_home_template.html", context)
    except Students.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect('doLogin')





def student_view_attendance(request):
    try:
        student = Students.objects.get(admin=request.user.id)
        courses = student.courses.all()
        groups = Group.objects.filter(students=student)

        attendance_data = AttendanceReport.objects.filter(
            student_id=student,
            attendance_id__course__in=courses,
            attendance_id__group__in=groups
        ).select_related('attendance_id', 'attendance_id__group')

        context = {
            "attendance_data": attendance_data,
            "student": student,
        }
    except Students.DoesNotExist:
        context = {
            "attendance_data": None,
            "student": None,
        }
    
    return render(request, "student_template/student_view_attendance.html", context)






def student_profile(request):
    user = CustomUser.objects.get(id=request.user.id)
    student = Students.objects.get(admin=user)

    context = {
        "user": user,
        "student": student
    }
    return render(request, 'student_template/student_profile.html', context)


def student_profile_update(request):
    if request.method != "POST":
        messages.error(request, "Invalid Method!")
        return redirect('student_profile')
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

            student = Students.objects.get(admin=customuser.id)
            student.address = address
            student.save()

            messages.success(request, "Profile Updated Successfully")
            return redirect('student_profile')
        except:
            messages.error(request, "Failed to Update Profile")
            return redirect('student_profile')





def get_student_notes(request):
    user = request.user

    try:
        student = Students.objects.get(admin=user)
    except Students.DoesNotExist:
        messages.error(request, "Student not found.")
        return HttpResponse("Student not found", status=404)

    courses = student.courses.all()
    all_notes = []

    for course in courses:
        assignment_note = Note.objects.filter(
            student=student, course=course, note_type=NoteType.ASSIGNMENT
        ).first()
        exam_note = Note.objects.filter(
            student=student, course=course, note_type=NoteType.EXAM
        ).first()

        assignment_value = float(assignment_note.content) if assignment_note else 0.0
        exam_value = float(exam_note.content) if exam_note else 0.0
        total_notes = assignment_value + exam_value

        absences = AttendanceReport.objects.filter(
            student_id=student,
            attendance_id__course=course,
            attendance_id__group__students=student,  # Ensure correct group filtering
            status=False  # Status should be False for absences
        ).count()

        adjusted_total = total_notes - absences
        final_result = adjusted_total / 3

        all_notes.append({
            'course_name': course.course_name,
            'assignment_note': assignment_value,
            'exam_note': exam_value,
            'absent_count': absences,
            'final_result': final_result,
        })

    context = {
        'student_name': student.admin.username,
        'all_notes': all_notes,
    }
    return render(request, 'student_template/get_student_notes.html', context)


def preview_certificate(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    student = get_object_or_404(Students, id=project.student.id)

    # Check if a certificate already exists for the project
    certificate, created = Certificat.objects.get_or_create(
        student=student,
        project=project,  # Include the project here
        defaults={
            'organization_name': 'C.M.C.F',
            # other fields can be initialized here if necessary
        }
    )

    # If the certificate was newly created, generate the PDF and save it
 
    buffer = generate_certificate(
            student_name=f'{student.admin.last_name} {student.admin.first_name}',
            ppr=student.code_PPR,
            reference=student.reference,
            project_title=project.title,
            trainer_name=f"{project.encadrant.admin.last_name}, {project.encadrant.admin.first_name}",
            include_signature=True  # or some condition to include signature
        )
        
       
    certificate.save()
    

    # Return the certificate as a downloadable PDF
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificate_{project_id}.pdf"'
    return response

