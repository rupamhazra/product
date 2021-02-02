from pms import views
from django.conf.urls import url, include
#from rest_framework import routers
from django.urls import path

urlpatterns = [
#   :::::::::::::::::  ATTENDENCE ::::::::::::::::::::#
    # path('attandance_login/', views.AttendanceLoginView.as_view()),
    path('attandance_logout/<pk>/', views.AttendanceLogOutView.as_view()),
    path('attandance_add/', views.AttendanceAddView.as_view()),
    # path('attandance_add_new/', views.AttendanceNewAddView.as_view()),
    #modification 09/09/2019
    # path('attandance_offline_add/', views.AttendanceOfflineAddView.as_view()),
    path('attandance_list_by_employee/<employee_id>/', views.AttendanceListByEmployeeView.as_view()),
    path('attandance_summary_by_employee/<employee_id>/', views.AttendanceSummaryByEmployeeView.as_view()),
    path('attandance_edit/<pk>/', views.AttendanceEditView.as_view()),
    path('attandance_approval_list/', views.AttendanceApprovalList.as_view()),
    path('attandance_approval_log_list/', views.AttandanceAllDetailsListView.as_view()),

    # for permisson label added by @Rupam
    path('attandance_approval_log_list_by_permisson/', views.AttandanceAllDetailsListByPermissonView.as_view()),

    # for permisson label added by @Rupam
    path('attandance_approval_list_with_only_deviation_by_permisson/', views.AttandanceListWithOnlyDeviationByPermissonView.as_view()),

    #::::::::::::::::: PmsAttandanceLog ::::::::::::::::::::#
    path('attandance_log_add/', views.AttandanceLogAddView.as_view()),
    path('attandance_log_multiple_add/', views.AttandanceLogMultipleAddView.as_view()),
    path('attandance_log_edit/<pk>/', views.AttendanceLogEditView.as_view()),
    path('attandance_log_approval_edit/<pk>/', views.AttandanceLogApprovalEditView.as_view()),

    #:::::::::::::::::  PmsLeaves ::::::::::::::::::::#
    path('advance_leave_apply/', views.AdvanceLeaveAddView.as_view()),
    path('advance_leave_apply_edit/<pk>/', views.AdvanceLeaveEditView.as_view()),
    path('advance_leave_mass_apply_edit/', views.AdvanceLeaveMassEditView.as_view()),
    path('leave_list_by_employee/<employee_id>/', views.LeaveListByEmployeeView.as_view()),

    # --------------------------- Pms Attandance Deviation------------------------------------
    path('attandance_deviation_justification/<pk>/', views.AttandanceDeviationJustificationEditView.as_view()),
    path('attandance_deviation_approval/<pk>/', views.AttandanceDeviationApprovaEditView.as_view()),
    path('attandance_mass_deviation_approval/', views.AttandanceMassDeviationApprovaEditView.as_view()),
    path('attandance_deviation_by_attandance_list/', views.AttandanceDeviationByAttandanceListView.as_view()),

    #:::::::::::::::::::::: PMS EMPLOYEE CONVEYANCE:::::::::::::::::::::::::::#
    path('employee_conveyance_add/', views.EmployeeConveyanceAddView.as_view()),
    path('employee_conveyance_edit/<pk>/', views.EmployeeConveyanceEditView.as_view()),
    path('employee_conveyance_list/', views.EmployeeConveyanceListView.as_view()),

    #:::::::::::::::::::::::::::::::::::PMS EMPLOYEE FOODING:::::::::::::::::::::::::::::::#
    path('employee_fooding_add/', views.EmployeeFoodingAddView.as_view()),
    path('attandance_approval_log_list_with_fooding/', views.AttandanceAllDetailsListWithFoodingView.as_view()),

    #:::::::::::::::::::::::::::::::: ATTENDENCE LIST EXPORT ::::::::::::::::::::::::::::::#
    path('attandance_list_export/', views.AttandanceListExportView.as_view()),

    
    #Added By Rupam Hazra on [10-01-2020] line number 58
    
    path('attandance_update_logout_time_failed_on_logout/<pk>/', views.AttendanceUpdateLogOutTimeFailedOnLogoutView.as_view()),
    path('attandance_log_multiple_by_thread_add/', views.AttandanceLogMultipleByThreadAddView.as_view()),

    #:::::::::::::::::::::::::::::::: ATTENDENCE SAP REPORT ::::::::::::::::::::::::::::::#
    path('tdms_attandance_sap_report/', views.PmsAttandanceSAPExportView.as_view()),

    #:::::::::::::::::::: L I V E   T R A C K I N G :::::::::::::::::#
    path('tdms_live_tracking_for_all_employees/<project_id>/', views.PmsLiveTrackingForAllEmployeesView.as_view()),
    path('tdms_live_tracking_for_a_employee_in_project/<employee_id>/', views.PmsLiveTrackingForAEmployeeInAProjectView.as_view()),



    #::::::::::::::::::::: N E W   A T T E N D A N C E   S Y S T E M :::::::::::::::#
    
    # Cron API for Absent User
    path('absent_attendance_insert_cron/', views.AbsentAttendanceInsertCronView.as_view()),
    
    # Logout
    path('v2/attandance_logout/<pk>/', views.AttendanceLogOutV2View.as_view()),

    # Login
    path('v2/attandance_add/', views.AttendanceAddV2View.as_view()),
    
    # Daily Attendance List
    path('v2/attandance_list_by_employee/<employee_id>/', views.AttendanceListByEmployeeV2View.as_view()),

    # Daily Attendance Summary
    path('v2/attandance_summary_by_employee/<employee_id>/', views.AttendanceSummaryByEmployeeV2View.as_view()),

    # Apply daily attendance justification
    path('v2/attandance_deviation_justification/<pk>/',views.AttandanceDeviationJustificationV2EditView.as_view()), # For Attendance apply
    

    # Report #
    path('v2/attandance_approval_log_list_by_permisson/', views.AttandanceAllDetailsListByPermissonV2View.as_view()),
    
    # Aprroval #
    path('v2/attandance_approval_list_with_only_deviation_by_permisson/', views.AttandanceListWithOnlyDeviationByPermissonV2View.as_view()),
    
    
    #path('v2/attandance_update_logout_time_failed_on_logout/<pk>/', views.AttendanceUpdateLogOutTimeFailedOnLogoutV2View.as_view()), # this API has not been used due to adding multiple login & logout functionality

    # Fortnight Attendance Summery
    path('v2/tdms_flexi_team_fortnight_attendance/',views.PmsFlexiTeamFortnightAttendance.as_view()),
    
    # Approval by Team Lead 
    path('v2/attandance_deviation_approval/', views.AttandanceDeviationApprovaEditV2View.as_view()),

    # Calucation for Leave Part for Daily Attendance Section
    path('v2/tdms_attendance_grace_leave_list_first_modified/', views.PmsAttendanceGraceLeaveListModifiedV2View.as_view()),


    path('v2/tdms_attendance_leave_approval_list/',views.PmsAttendanceLeaveApprovalListV2View.as_view()), # team
    
    # Generate SAP Report
    path('v2/tdms_attendance_admin_sap_report/',views.PmsAttandanceAdminSAPReportView.as_view()),

    # Generate OS/MIS Report
    path('v2/tdms_attendance_admin_od_mis_report/',views.PmsAttandanceAdminOdMsiReportView.as_view()),

    # Advance Leave Apply
    path('v2/tdms_attendance_advance_leave_add/',views.PmsAttendanceAdvanceLeaveAddV2View.as_view()),
    
    # Attendance Fortnight Cron API
    path('attendance/cron/', views.PmsAttendanceCronView.as_view()),

    # Leave Balance insert for transfer a user from PMS to HRMS upto transfer date
    
    path('attendance/add/leave_balance_for_transfer_user/', views.PmsAttendanceLeaveBalanceTransferUserView.as_view()),

]
