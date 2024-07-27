
from django.contrib.auth.models import AbstractUser
from django.db import IntegrityError, models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models.signals import m2m_changed
from django.utils import timezone
from django.db.models import Avg, F, FloatField, Sum
from django.utils.functional import cached_property
from django.urls import reverse
from django.utils.html import format_html
from datetime import time
import random



# Overriding the Default Django Auth User and adding One More Field (user_type)
class CustomUser(AbstractUser):
    user_type_data = ((1, "HOD"), (2, "Staff"), (3, "Student"))
    user_type = models.CharField(default=1, choices=user_type_data, max_length=10)

class AdminHOD(models.Model):
    id = models.AutoField(primary_key=True)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='adminhod')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()
    
    def generate_certificate_link(self, obj):
        # If the HOD can generate certificates for all students
        url = reverse('generate_certificate')  # You can adjust this if needed
        return format_html('<a href="{}" target="_blank">Generate Certificates</a>', url)
    generate_certificate_link.short_description = 'Generate Certificates'


class Courses(models.Model):
    id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    def __str__(self):
        return self.course_name
    
    def delete(self, *args, **kwargs):
        for student in self.students.all():
            student.courses.remove(self)
        super().delete(*args, **kwargs)

class Group(models.Model):
    DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    CATEGORY_CHOICES = [
        ('Morning', 'Morning'),
        ('Evening', 'Evening'),
    ]

    id = models.AutoField(primary_key=True)
    day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    courses = models.ManyToManyField('Courses')  # Assuming Courses model is defined elsewhere
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    def __str__(self):
        return f"{self.day_of_week} {self.category} Group"

    @staticmethod
    def create_initial_schedule(group):
        # Fetch all courses since all groups (morning/evening) should include all courses
        courses = Courses.objects.all()
        
        # Define the start and end times based on the group's category
        if group.category == 'Morning':
            start_time = '09:00:00'  # Example morning start time
            end_time = '12:00:00'    # Example morning end time
        else:  # Evening
            start_time = '14:00:00'  # Example evening start time
            end_time = '17:00:00'    # Example evening end time
        
        for course in courses:
            try:
                # Create a GroupSchedule for each course if it doesn't already exist
                GroupSchedule.objects.get_or_create(
                    group=group,
                    course=course,
                    day_of_week=group.day_of_week,
                    start_time=start_time,
                    end_time=end_time,
                    category=group.category
                )
            except IntegrityError:
                print(f"Schedule already exists for group {group}, course {course}. Skipping creation.")



class GroupSchedule(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    course = models.ForeignKey('Courses', on_delete=models.CASCADE)
    day_of_week = models.CharField(max_length=10, choices=Group.DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    category = models.CharField(max_length=10, choices=Group.CATEGORY_CHOICES)

    class Meta:
        unique_together = ('group', 'day_of_week', 'start_time', 'end_time', 'category')

    def __str__(self):
        return f"{self.group} - {self.course} ({self.category}) on {self.day_of_week} from {self.start_time} to {self.end_time}"



class GroupSchedule(models.Model):
    CATEGORY_CHOICES = [
        ('Morning', 'Morning'),
        ('Evening', 'Evening'),
    ]

    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)
    day_of_week = models.CharField(max_length=10, choices=Group.DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)

    class Meta:
        unique_together = ('group', 'day_of_week', 'start_time', 'end_time', 'category')

    def __str__(self):
        return f"{self.group} - {self.course} ({self.category}) on {self.day_of_week} from {self.start_time} to {self.end_time}"

        

class Staffs(models.Model):
    id = models.AutoField(primary_key=True)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='staffs')
    gender = models.CharField(max_length=50,default="male")
    profile_pic = models.FileField(default=" ")
    address = models.TextField()
    course = models.ForeignKey(Courses, on_delete=models.DO_NOTHING,default=1)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()




class Students(models.Model):
    id = models.AutoField(primary_key=True)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='students')
    gender = models.CharField(max_length=50)
    profile_pic = models.FileField()
    address = models.TextField()
    courses = models.ManyToManyField(Courses, related_name='students')
    preferred_category = models.CharField(max_length=10, choices=[('morning', 'Morning'), ('evening', 'Evening')])  
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True)
    grade = models.CharField(max_length=20, choices=[
        ('primaire', 'Primaire'),
        ('college', 'Collège'),
        ('lycee', 'Lycée'),
        ('universite', 'Université'),
        ('superieure', 'Supérieure')
    ])
    code_PPR = models.CharField(max_length=50, null=True,unique=True)
    reference= models.CharField(max_length=100,default="Rabat Sale zamour zaer")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    def __str__(self):
        return f"{self.admin.last_name} {self.admin.first_name}"


class NoteType(models.TextChoices):
    ASSIGNMENT = 'A', 'Assignment'
    EXAM = 'E', 'Exam'

class Note(models.Model):
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)
    note_date = models.DateField(default=timezone.now)
    note_type = models.CharField(max_length=1, choices=NoteType.choices,default="A")
    content = models.TextField(default="0.00")

    def __str__(self):
        return f'Note for {self.student.admin.username} in {self.course.course_name} - {self.get_note_type_display()}'

class Attendance(models.Model):
    id = models.AutoField(primary_key=True)
    attendance_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    course = models.ForeignKey(Courses, on_delete=models.CASCADE, default=1)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    objects = models.Manager()

class AttendanceReport(models.Model):
    # Individual Student Attendance
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Students, on_delete=models.DO_NOTHING)
    attendance_id = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()



class Certificat(models.Model):
    student = models.ForeignKey(Students, on_delete=models.CASCADE, related_name='certificates')
    certificate_file = models.FileField(upload_to='certificates/')
    course_date = models.DateField(default=timezone.now)      
    course_name = models.CharField(max_length=255)
    staff_name = models.CharField(max_length=255)
    grade = models.CharField(max_length=50)
    feedback = models.TextField()
    organization_name = models.CharField(max_length=255, default='C.M.C.F')
    director_signature = models.ImageField(upload_to='signatures/', null=True, blank=True)



class NotificationStudent(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Students, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()



class NotificationStaffs(models.Model):
    id = models.AutoField(primary_key=True)
    stafff_id = models.ForeignKey(Staffs, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()



class StudentResult(models.Model):
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @cached_property
    def total_score(self):
        # Aggregate all the notes related to this student and course
        notes = Note.objects.filter(student=self.student, course=self.course)
        total = notes.aggregate(total=Sum(F('note_type') * F('content'), output_field=FloatField()))
        return total['total'] if total['total'] is not None else 0.0

    @cached_property
    def average_score(self):
        # Calculate the average of all the notes related to this student and course
        notes = Note.objects.filter(student=self.student, course=self.course)
        average = notes.aggregate(average=Avg('content', output_field=FloatField()))
        return average['average'] if average['average'] is not None else 0.0

    def __str__(self):
        return f"Result for {self.student.admin.username} in {self.course.course_name}"



class Project(models.Model):
    title = models.CharField(max_length=555)
    encadrant = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, limit_choices_to={'user_type': 2}, related_name='projects_as_encadrant')
    student = models.ForeignKey('Students', on_delete=models.SET_NULL, null=True, related_name='projects')
    certificate_generated = models.BooleanField(default=False)
    def __str__(self):
        return self.title
    








@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 1:  # AdminHOD
            AdminHOD.objects.create(admin=instance)
        elif instance.user_type == 2:  # Staff
            try:
                default_course = Courses.objects.get(id=1)  # Replace with default course ID
                Staffs.objects.create(admin=instance, course=default_course, address="")
            except Courses.DoesNotExist:
                pass  # Handle case where default course does not exist
        elif instance.user_type == 3:  # Student
            Students.objects.create(admin=instance)

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    if instance.user_type == 1:
        if hasattr(instance, 'adminhod'):
            instance.adminhod.save()
    elif instance.user_type == 2:
        if hasattr(instance, 'staffs'):
            instance.staffs.save()
    elif instance.user_type == 3:
        if hasattr(instance, 'students'):
            instance.students.save()


@receiver(m2m_changed, sender=Students.courses.through)
def courses_changed(sender, instance, action, reverse, **kwargs):
    if action == 'post_remove':
        instance.courses.clear()