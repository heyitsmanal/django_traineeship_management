from django.apps import AppConfig

class StudentManagementAppConfig(AppConfig):
    name = 'student_management_app'

    def ready(self):
        import student_management_app.signals