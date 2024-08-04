from django.core.management.base import BaseCommand
from random import shuffle
from student_management_app.models import Staffs, Group

class Command(BaseCommand):
    help = 'Assign staff members to groups randomly'

    def handle(self, *args, **kwargs):
        groups = Group.objects.all()

        # Shuffle groups to assign staff randomly
        group_list = list(groups)
        shuffle(group_list)

        staff_members = Staffs.objects.all()

        for index, staff in enumerate(staff_members):
            # Assign staff to a group (randomly)
            assigned_group = group_list[index % len(group_list)]
            staff.group = assigned_group
            staff.save()

        self.stdout.write(self.style.SUCCESS('Successfully assigned staff to groups randomly'))
