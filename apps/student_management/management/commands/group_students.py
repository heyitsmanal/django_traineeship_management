from django.db.models import Count
from django.core.management.base import BaseCommand
from apps.student_management.models import Students, Courses, Group
import random

class Command(BaseCommand):
    help = 'Group students into school groups based on the provided criteria.'

    def add_arguments(self, parser):
        parser.add_argument('--min-groups-morning', type=int, default=5, help='Minimum number of morning groups')
        parser.add_argument('--max-groups-morning', type=int, default=5, help='Maximum number of morning groups')
        parser.add_argument('--min-groups-evening', type=int, default=5, help='Minimum number of evening groups')
        parser.add_argument('--max-groups-evening', type=int, default=5, help='Maximum number of evening groups')
        parser.add_argument('--avoid-days', nargs='+', type=int, help='Days to avoid having groups (0=Monday, 6=Sunday)')
        parser.add_argument('--create-days', nargs='+', type=int, help='Days to create groups (0=Monday, 6=Sunday)')

    def handle(self, *args, **options):
        min_groups_morning = options['min_groups_morning']
        max_groups_morning = options['max_groups_morning']
        min_groups_evening = options['min_groups_evening']
        max_groups_evening = options['max_groups_evening']
        avoid_days = options['avoid_days']
        create_days = options['create_days']
        
        courses = Courses.objects.all()
        for course in courses:
            students = Students.objects.filter(course=course)
            morning_students = students.filter(preferred_category='morning')
            evening_students = students.filter(preferred_category='evening')
            
            self.group_students(course, morning_students, 'morning', min_groups_morning, max_groups_morning, avoid_days, create_days)
            self.group_students(course, evening_students, 'evening', min_groups_evening, max_groups_evening, avoid_days, create_days)

    def group_students(self, course, students, category, min_groups, max_groups, avoid_days, create_days):
        existing_groups = Group.objects.filter(course=course, category=category)
        group_capacity = 14
        min_group_size = 8
        
        # Get all students already assigned to groups in this category
        students_in_groups = Students.objects.filter(course=course, preferred_category=category, group__isnull=False)
        
        # Remove students from their existing groups
        for student in students_in_groups:
            student.group = None
            student.save()
        
        # Shuffle students for randomness
        students = list(students)
        random.shuffle(students)
        
        groups = []
        
        while students:
            # Create new groups if none exist or reassign students to existing groups
            if existing_groups.exists():
                groups = list(existing_groups.annotate(num_students=Count('students')).order_by('num_students'))
                for student in students:
                    smallest_group = groups[0]
                    if smallest_group.num_students < group_capacity:
                        student.group = smallest_group
                        student.save()
                        smallest_group.students.add(student)
                    else:
                        new_group = Group.objects.create(course=course, category=category, day_of_week=create_days[0] if create_days else 0)
                        new_group.students.add(student)
                        groups.append(new_group)
                        students.remove(student)
            else:
                new_group = Group.objects.create(course=course, category=category, day_of_week=create_days[0] if create_days else 0)
                new_group.students.add(students.pop(0))
                groups.append(new_group)
