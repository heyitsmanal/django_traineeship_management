
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static
from . import views
from . import HodViews, StaffViews, StudentViews
from django.contrib.auth import views as auth_views

from django.views.i18n import set_language


urlpatterns = [
    # path('accounts/', include('django.contrib.auth.urls')),
    path('', views.homepage, name="homepage"),
    path('login/', views.loginPage, name="login"),
    path('doLogin/', views.doLogin, name="doLogin"),
    path('enroll-student/', views.enroll_student, name='enroll_student'),
    path('enroll-success/', views.enroll_success, name='enroll_success'),
    path('get_user_details/', views.get_user_details, name="get_user_details"),
    path('contact/', views.contact, name='contact'),

    path('reinitialisation/', views.CustomPasswordResetView.as_view(), name='custom_password_reset'),
    path('reinitialisation/reussite/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reinitialisation/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(),
	 name='password_reset_confirm'),
    path('reinitialisation/complet/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
   
    path('set_language/', set_language, name='set_language'),
  

    path('delete_excessive_absences/', HodViews.delete_students_with_excessive_absences, name='delete_students_with_excessive_absences'),
    path('manage_timetable/', HodViews.manage_timetable, name='manage_timetable'),
    path('group_timetable/<int:group_id>/', HodViews.group_timetable, name='group_timetable'),
    path('delete_schedule/<int:schedule_id>', HodViews.delete_schedule, name="delete_schedule"),
    path('delete_group/<int:group_id>/', HodViews.delete_group, name='delete_group'),
    path('logout_user/', views.logout_user, name="logout_user"),
    path('admin_home/', HodViews.admin_home, name="admin_home"),
    path('add_student/', HodViews.add_student, name="add_student"),
    path('add_student_save/', HodViews.add_student_save, name="add_student_save"),
    path('manage_student/', HodViews.manage_student, name="manage_student"),
    path('edit_student/<student_id>/', HodViews.edit_student, name="edit_student"),
    path('edit_student_save/', HodViews.edit_student_save, name="edit_student_save"),
    path('delete_student/<student_id>/', HodViews.delete_student, name="delete_student"),
    path('check_email_exist/', HodViews.check_email_exist, name='check_email_exist'),
    path('check_code_PPR_exist/', HodViews.check_code_PPR_exist, name='check_code_PPR_exist'),
    path('check_username_exist/', HodViews.check_username_exist, name='check_username_exist'),
    path('add_staff/', HodViews.add_staff, name="add_staff"),
    path('add_staff_save/', HodViews.add_staff_save, name="add_staff_save"),
    path('manage_staff/', HodViews.manage_staff, name="manage_staff"),
    path('edit_staff/<staff_id>/', HodViews.edit_staff, name="edit_staff"),
    path('edit_staff_save/', HodViews.edit_staff_save, name="edit_staff_save"),
    path('delete_staff/<staff_id>/', HodViews.delete_staff, name="delete_staff"),
    path('add_course/', HodViews.add_course, name="add_course"),
    path('add_course_save/', HodViews.add_course_save, name="add_course_save"),
    path('manage_course/', HodViews.manage_course, name="manage_course"),
    path('edit_course/<course_id>/', HodViews.edit_course, name="edit_course"),
    path('edit_course_save/', HodViews.edit_course_save, name="edit_course_save"),
    path('delete_course/<course_id>/', HodViews.delete_course, name="delete_course"),
    path('admin_view_attendance/', HodViews.admin_view_attendance, name="admin_view_attendance"),
    path('admin_get_attendance_courses/', HodViews.admin_get_attendance_courses, name="admin_get_attendance_courses"),
    path('admin_profile/', HodViews.admin_profile, name="admin_profile"),
    path('admin_profile_update/', HodViews.admin_profile_update, name="admin_profile_update"),
    path('manage_staff_groups/', HodViews.manage_staff_groups, name='manage_staff_groups'),
    path('manage_student_groups/', HodViews.manage_student_groups, name='manage_student_groups'),
    path('update_student_group/', HodViews.update_student_group, name='update_student_group'),
    path('update_staff_group/', HodViews.update_staff_group, name='update_staff_group'),
    path('manage_groups/', HodViews.manage_groups, name='manage_groups'),
    path('group/<int:group_id>/', HodViews.group_detail, name='group_detail'),
    path('manage-student-groups/', HodViews.manage_student_groups, name='manage_student_groups'),
    path('update-student-group/', HodViews.update_student_group, name='update_student_group'),
    path('add_group/', HodViews.add_group, name='add_group'),
    path('generate_certificate/<int:project_id>/', HodViews.generate_certificate_view, name='generate_certificate'),
    path('print_certificates/', HodViews.print_certificate_template, name='print_certificate_template'),
    path('admin_get_group_students/', HodViews.admin_get_group_students, name='admin_get_group_students'),

    


    # URLS for Staff
    path('staff_home/', StaffViews.staff_home, name="staff_home"),
    path('staff_take_attendance/', StaffViews.staff_take_attendance, name='staff_take_attendance'),
    path('get_students/<int:groupid>/', StaffViews.get_students, name='get_students'),
    path('save_attendance_data/', StaffViews.save_attendance_data, name="save_attendance_data"),
    path('staff_profile/', StaffViews.staff_profile, name="staff_profile"),
    path('staff_profile_update/', StaffViews.staff_profile_update, name="staff_profile_update"),
    path('add_note/', StaffViews.staff_add_note, name="add_note"),
    path('save_notes_data/', StaffViews.save_notes_data, name="save_notes_data"),
    path('get_groups/<int:course_id>/', StaffViews.get_groups, name='get_groups'),
    path('list_attendances/<int:course_id>/<int:group_id>/', StaffViews.list_attendances, name='list_attendances'),
    path('view_attendance/<int:attendance_id>/', StaffViews.view_attendance, name='view_attendance'),
    path('validate_project/', StaffViews.validate_project, name='validate_project'),
    path('delete_project/<int:project_id>/', StaffViews.delete_project, name='delete_project'),

    # path('search_students/', StaffViews.search_students, name='search_students'),



    # URSL for Student
    path('student_home/', StudentViews.student_home, name="student_home"),
    path('student_view_attendance/', StudentViews.student_view_attendance, name="student_view_attendance"),
    path('student_profile/', StudentViews.student_profile, name="student_profile"),
    path('student_profile_update/', StudentViews.student_profile_update, name="student_profile_update"),
    path('certificate/preview/<int:project_id>/', StudentViews.preview_certificate, name='preview_certificate'),
    path('notes/', StudentViews.get_student_notes, name='get_student_notes'),


    # path('student_view_result/', StudentViews.student_view_result, name="student_view_result"),
]
