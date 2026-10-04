from django.apps import AppConfig

class StudentManagementAppConfig(AppConfig):
	default_auto_field = "django.db.models.BigAutoField"
    	name = "apps.student_management"  

    	label = "student_management_app" 
    	verbose_name = "Student Management"

    def ready(self):
        import apps.student_management.signals