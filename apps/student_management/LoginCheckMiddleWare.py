from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import render, redirect
from django.urls import reverse


class LoginCheckMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        modulename = view_func.__module__
        user = request.user

        # List of URL names that should be accessible without authentication
        allowed_urls = [
            reverse("login"),
            reverse("doLogin"),
            reverse("enroll_student"),
            reverse("homepage"),
            reverse("custom_password_reset"),
            reverse("password_reset_done"),
            reverse("password_reset_confirm", kwargs={'uidb64': 'dummy', 'token': 'dummy'}),
            reverse("password_reset_complete")
        ]

        # Allow access to the specified views
        if request.path in allowed_urls:
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
            # Redirect unauthenticated users to the login page unless it's an allowed URL
            return redirect("login")