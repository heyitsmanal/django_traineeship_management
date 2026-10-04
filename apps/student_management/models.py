
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



class Day(models.Model):
    DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    name = models.CharField(max_length=10, choices=DAYS_OF_WEEK, unique=True)

    def __str__(self):
        return self.name

class GroupSchedule(models.Model):
    group = models.ForeignKey('Group', on_delete=models.CASCADE)
    course = models.ForeignKey('Courses', on_delete=models.CASCADE)
    day_of_week = models.ForeignKey('Day', on_delete=models.CASCADE)  # Use ForeignKey to Day model
    start_time = models.TimeField()
    end_time = models.TimeField()
    category = models.CharField(
        max_length=10,
        choices=[('Morning', 'Morning'), ('Evening', 'Evening')]
    )

    class Meta:
        unique_together = ('group', 'course', 'day_of_week', 'start_time', 'end_time', 'category')
        verbose_name = 'Group Schedule'
        verbose_name_plural = 'Group Schedules'

    def __str__(self):
        return f"{self.group} - {self.course} ({self.category}) on {self.day_of_week} from {self.start_time} to {self.end_time}"

 

class Group(models.Model):
    CATEGORY_CHOICES = [
        ('Morning', 'Morning'),
        ('Evening', 'Evening'),
    ]

    id = models.AutoField(primary_key=True)
    days_of_week = models.ManyToManyField(Day)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    courses = models.ManyToManyField('Courses') 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    def _str_(self):
        return f"{self.category} Group"

    def create_initial_schedule(self):
        courses = list(self.courses.all())
        days_of_week = list(self.days_of_week.all())

        if self.category == 'Morning':
            time_slots = [('08:30', '10:30'), ('10:45', '12:30')]  # Morning session times
        else:
            time_slots = [('13:30', '15:00'), ('15:15', '16:30')]  # Evening session times

        used_courses = set()
        used_days = set()

        for course in courses:
            if course in used_courses:
                continue  # Skip if the course is already scheduled

            for day in days_of_week:
                if day in used_days:
                    continue  # Skip if the day is already used

                for start_time, end_time in time_slots:
                    # Ensure we do not assign overlapping schedules for the same day
                    if not GroupSchedule.objects.filter(
                        group=self, day_of_week=day, start_time=start_time, end_time=end_time
                    ).exists():
                        GroupSchedule.objects.create(
                            group=self,
                            course=course,
                            day_of_week=day,
                            start_time=start_time,
                            end_time=end_time,
                            category=self.category
                        )
                        print(f"Schedule created for group {self}, course {course}, day {day}.")
                        used_courses.add(course)
                        used_days.add(day)
                        break  # Move to the next course after scheduling


@receiver(post_save, sender=Group)
def group_created_handler(sender, instance, created, **kwargs):
    if created:
        instance.create_initial_schedule()




       

class Staffs(models.Model):
    id = models.AutoField(primary_key=True)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='staffs')
    gender = models.CharField(max_length=50,default="male")
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    address = models.TextField()
    course = models.ForeignKey(Courses, on_delete=models.DO_NOTHING,default=1)
    groups = models.ManyToManyField(Group)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()




class Students(models.Model):
    id = models.AutoField(primary_key=True)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='students')
    gender = models.CharField(max_length=50)
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
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
    # blacklisted = models.BooleanField(default=False)
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

class Project(models.Model):
    title = models.CharField(max_length=555)
    encadrant = models.ForeignKey(Staffs, on_delete=models.SET_NULL, null=True, blank=True)
    student = models.ForeignKey('Students', on_delete=models.SET_NULL, null=True, related_name='projects')
    certificate_generated = models.BooleanField(default=False)
    def __str__(self):
        return self.title
    
class Certificat(models.Model):
    student = models.ForeignKey(Students, on_delete=models.CASCADE, related_name='certificates')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='certificates',default="1")  # Add this line
    organization_name = models.CharField(max_length=255, default='C.M.C.F')




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



class BlacklistedStudent(models.Model):
    student = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    reason = models.CharField(max_length=255)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.reason}"




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