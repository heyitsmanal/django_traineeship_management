from io import BytesIO
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

from student_management_app.models import Certificat, CustomUser, Group, Note, NoteType, Project, Staffs, Courses, StudentResult, Students, Attendance, AttendanceReport
from student_management_app.utils import generate_certificate



def student_home(request):
    try:
        # Fetch the student object
        student_obj = Students.objects.get(admin=request.user)

        # Calculate total attendance
        total_attendance = AttendanceReport.objects.filter(student_id=student_obj.id).count()
        attendance_present = AttendanceReport.objects.filter(student_id=student_obj.id, status=True).count()
        attendance_absent = AttendanceReport.objects.filter(student_id=student_obj.id, status=False).count()

        # Calculate attendance by course
        courses = student_obj.courses.all()  # Get all courses for the student
        total_attendance_by_course = 0
        for course in courses:
            total_attendance_by_course += Attendance.objects.filter(course=course).count()


            certificate = Certificat.objects.filter(student=student_obj).first()

            context = {
            'certificate': certificate,
            "total_attendance": total_attendance,
            "attendance_present": attendance_present,
            "attendance_absent": attendance_absent,
            "total_attendance_by_course": total_attendance_by_course,
        }
        return render(request, "student_template/student_home_template.html", context)
    except Students.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect('doLogin')


def student_view_attendance(request):
    try:
        # Fetch the logged-in student
        student = Students.objects.get(admin=request.user.id)
        # Get all courses the student is enrolled in
        courses = student.courses.all()

        # Get the groups the student is part of
        groups = Group.objects.filter(students=student)

        # Retrieve attendance data for the student's courses and groups
        attendance_data = AttendanceReport.objects.filter(
            student_id=student,
            attendance_id__course__in=courses,
            attendance_id__group__in=groups
        ).select_related('attendance_id', 'attendance_id__group')

        # Context for rendering the template
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
        # Fetch assignment and exam notes for the course
        assignment_note = Note.objects.filter(
            student=student, course=course, note_type=NoteType.ASSIGNMENT
        ).first()
        exam_note = Note.objects.filter(
            student=student, course=course, note_type=NoteType.EXAM
        ).first()

        # Default to 0 if the note doesn't exist
        assignment_value = float(assignment_note.content) if assignment_note else 0.0
        exam_value = float(exam_note.content) if exam_note else 0.0

        # Sum the notes
        total_notes = assignment_value + exam_value

        # Fetch attendance records and count absences specific to this course
        absences = AttendanceReport.objects.filter(
            student_id=student,
            attendance_id__course=course,
            attendance_id__group__students=student,  # Ensure correct group filtering
            status=True
        ).count()

        # Subtract the number of absences from the total notes
        adjusted_total = total_notes - absences

        # Final result calculation
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




def preview_certificate(request, certificate_id):
    try:
        certificate = Certificat.objects.get(id=certificate_id)
    except Certificat.DoesNotExist:
        return HttpResponse('Certificate not found', status=404)

    # Assuming each student has only one project associated with them
    projects = Project.objects.filter(student=certificate.student)
    
    if not projects:
        return HttpResponse('No project found for the student', status=404)
    
    # Extract the title from the first project in the queryset
    project_title = projects.first().title  # Assuming your Project model has a 'title' field
    
    # Generate the certificate with the signature included
    base_pdf_buffer = generate_certificate(
        student_name=f'{certificate.student.admin.first_name} {certificate.student.admin.last_name}',
        ppr=certificate.student.code_PPR,
        reference=certificate.student.reference,
        project_title=project_title,  # Pass the project title directly
        trainer_name=certificate.staff_name,
        include_signature=True  # Pass True to include the signature
    )
    
    response = HttpResponse(base_pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=certificate_{certificate_id}.pdf'
    return response

   

