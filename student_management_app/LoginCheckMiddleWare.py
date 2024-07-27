from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import render, redirect
from django.urls import reverse

class LoginCheckMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        modulename = view_func.__module__
        user = request.user

        if request.path in [reverse("login"), reverse("doLogin"), reverse("enroll_student"), reverse("homepage")]:
            return None

        if user.is_authenticated:
            if user.user_type == "1":
                if modulename == "student_management_app.HodViews":
                    return None
                elif modulename in ["student_management_app.views", "django.views.static"]:
                    return None
                else:
                    return redirect("admin_home")
            
            elif user.user_type == "2":
                if modulename == "student_management_app.StaffViews":
                    return None
                elif modulename in ["student_management_app.views", "django.views.static"]:
                    return None
                else:
                    return redirect("staff_home")
            
            elif user.user_type == "3":
                if modulename == "student_management_app.StudentViews":
                    return None
                elif modulename in ["student_management_app.views", "django.views.static"]:
                    return None
                else:
                    return redirect("student_home")

            else:
                return redirect("login")

        else:
            return redirect("login")