from django.urls import path
from attendance import views
from django.conf.urls import url, include
from rest_framework.authtoken import views as rest_framework_views

'''
    attendance_file_upload ::- Daily upload from Excel File 
    attendance_file_upload_for_new_user ::- This is for new user attendence from Postman Hit with excel file
    attendance_file_upload_check_by_punch_from_old_data_base ::- This is for user attendence from 
    old database using Postman hit with date range,punch_ids
    attendance_user_attendance_upload_by_log_data ::- this is used to correct
    attendence using attendence log table with empids,last_date
'''


urlpatterns = [
    #:::::::::::::::::::::: DEVICE MASTER:::::::::::::::::::::::::::#
    path('punch_device_master_add/', views.DeviceMasterAddView.as_view()),
    path('punch_device_master_edit/<pk>/', views.DeviceMasterEditView.as_view()),
    path('punch_device_master_delete/<pk>/', views.DeviceMasterDeleteView.as_view()),

	#:::::::::::::::::::::: ATTENDENCE MONTH MASTER:::::::::::::::::::::::::::#
    path('attendence_month_master_add/', views.AttendenceMonthMasterAddView.as_view()),
    path('attendence_month_master_edit/<pk>/', views.AttendenceMonthMasterEditView.as_view()),
    path('attendence_month_master_delete/<pk>/', views.AttendenceMonthMasterDeleteView.as_view()),
    
    path('attendence_approval_request/<pk>/',views.AttendenceApprovalRequestView.as_view()),

    #:::::::::::::::::::::::::::ATTENDANCE DOCUMENTS UPLOAD::::::::::::::::::::::::::::#
    
    path('attendance_file_upload/', views.AttendanceFileUpload.as_view()), #After modifications
    path('attendance_file_upload_for_new_user/', views.AttendanceFileUploadForNewUser.as_view()),
    
    path('attendance_file_upload_check_by_punch_from_old_data_base/', views.AttendanceFileUploadCheckPunchOldData.as_view()),
    path('attendance_user_attendance_upload_by_log_data/', views.AttendanceUserAttendanceUploadByLogData.as_view()),

    path('attendance_file_upload_old_version/', views.AttendanceFileUploadOldVersion.as_view()),
    path('attendance_file_upload_check/', views.AttendanceFileUploadCheck.as_view()),

    path('attendence_per_day_document/',views.AttendencePerDayDocumentAddView.as_view()),
    # path('attendence_per_day_document/',views.AttendencePerDayDocumentAddView.as_view()),
    # path('attendence_joining_approved_leave_add/',views.AttendenceJoiningApprovedLeaveAddView.as_view()),
    path('attendance_grace_leave_list_first/',views.AttendanceGraceLeaveListView.as_view()),
    path('attendance_grace_leave_list_first_modified/',views.AttendanceGraceLeaveListModifiedView.as_view()),

    path('attendance_late_conveyance_apply/<pk>/',views.AttendanceLateConveyanceApplyView.as_view()),
    path('attendance_late_conveyance_document_add/',views.AttendanceLateConveyanceDocumentAddView.as_view()),
    path('attendance_conveyance_approval_list/',views.AttendanceConveyanceApprovalListView.as_view()),
    
    path('attendance_conveyance_report_list/',views.AttendanceConveyanceAfterApprovalListView.as_view()),
    path('attendance_conveyance_report_list_export_download/',views.AttendanceConveyanceAfterApprovalListExportDownloadView.as_view()),
    
    path('attendance_summary_list/',views.AttendanceSummaryListView.as_view()),
    path('attendance_daily_list/',views.AttendanceDailyListView.as_view()),

    #:::::::::::::::::::::::::::ATTENDANCE ADVANCE LEAVE::::::::::::::::::::::::::::#
    path('attendance_advance_leave_list/',views.AttendanceAdvanceLeaveListView.as_view()),
    path('attendance_advance_leave_report/',views.AttendanceAdvanceLeaveReportView.as_view()),
    path('attendance_advance_leave_add/',views.AttendanceAdvanceLeaveAddView.as_view()),
    path('admin_attendance_advance_leave_pending_list/',views.AdminAttendanceAdvanceLeavePendingListView.as_view()),
    path('admin_attendance_advance_leave_approval/',views.AdminAttendanceAdvanceLeaveApprovalView.as_view()), 


    path('e_task_attendance_approval_list/',views.ETaskAttendanceApprovalList.as_view()),
    path('e_task_attendance_approval_grace_list/',views.ETaskAttendanceApprovaGracelList.as_view()),
    path('e_task_attendance_approval_withoout_grace_list/',views.ETaskAttendanceApprovaWithoutGracelList.as_view()),
    path('e_task_attendance_approval/',views.ETaskAttendanceApprovalView.as_view()),
    path('e_task_attendance_approval_modify/',views.ETaskAttendanceApprovalModifyView.as_view()),
    path('attendance_approval_report/',views.AttendanceApprovalReportView.as_view()),
    
    path('attendance_vehicle_type_master_add/',views.AttendanceVehicleTypeMasterAddView.as_view()),
    path('attendance_vehicle_type_master_edit/<pk>/',views.AttendanceVehicleTypeMasterEditView.as_view()),
    path('attendance_vehicle_type_master_delete/<pk>/',views.AttendanceVehicleTypeMasterDeleteView.as_view()),

    path('attendance_admin_summary_list/',views.AttendanceAdminSummaryListView.as_view()),

    path('attendance_admin_daily_list/',views.AttendanceAdminDailyListView.as_view()),

    path('attendance_leave_approval_list/',views.AttendanceLeaveApprovalList.as_view()),

    path('attendance_admin_mispunch_checker/',views.AttendanceAdminMispunchCheckerView.as_view()),#F-Complete
    path('attendance_admin_mispunch_checker_csv_report/',views.AttendanceAdminMispunchCheckerCSVReportView.as_view()),

    
    path('attendance_request_free_by_hr_list/',views.AttandanceRequestFreeByHRListView.as_view()),
    path('attendance_monthly_hr_list/',views.AttendanceMonthlyHRListView.as_view()),
    path('attendance_monthly_hr_summary_list/',views.AttendanceMonthlyHRSummaryListView.as_view()),#F-Complete
    path('attendance_grace_leave_list_for_hr_modified/',views.AttendanceGraceLeaveListForHRModifiedView.as_view()),#F-Complete
    #:::::::::::::::::::::::::::ATTENDANCE SPECIALDAY MASTER::::::::::::::::::::::::::::#
    path('attendence_special_day_master_add/', views.AttendanceSpecialdayMasterAddView.as_view()),
    path('attendence_special_day_master_edit/<pk>/', views.AttendanceSpecialdayMasterEditView.as_view()),
    path('attendence_special_day_master_delete/<pk>/', views.AttendanceSpecialdayMasterDeleteView.as_view()),
    path('attendance_employee_report/',views.AttendanceEmployeeReportView.as_view()),

    path('attendence_logs/',views.logListView.as_view()),

    #::::::::::::::::::::::::::::::::::::::: Report :::::::::::::::::::::::::::::::::::::::#
    path('attendance_admin_od_mis_report/',views.AttandanceAdminOdMsiReportView.as_view()),
    path('attendance_admin_od_mis_report_details/',views.AttandanceAdminOdMsiReportDetailsView.as_view()),
    path('attendance_admin_sap_report/',views.AttandanceAdminSAPReportView.as_view()),
    path('attendance_availed_grace_report/',views.AttandanceAvailedGraceReportView.as_view()),

    path('attendance_user_leave_report_till_date/',views.AttandanceUserLeaveReportTillDateView.as_view()),

    path('attendance_new_users_joining_leave_calculate_update/', views.AttendanceNewUsersJoiningLeaveCalculation.as_view()),

    ################################## cron testing api ##########################################
    path('attendance_user_cron_mail_for_pending_testapi/', views.AttendanceUserCronMailForPending.as_view()),
    path('attendance_user_cron_mail_for_pending_roh_testapi/', views.AttendanceUserCronMailForPendingRoh.as_view()),
    
    # Corn API (Monthly Auto Grace/Leave calculation)
    path('attendance_user_cron_lock_testapi/', views.AttendanceUserCronLock.as_view()),
    
    path('attendance_user_six_day_leave_checking/', views.AttendanceUserSixDayLeaveCheck.as_view()),

    # Dependent on celery and ($ celery -A SSIL_SSO_MS worker -l info) need to be executed
    path('email_sms_alert_for_request_approval/', views.EmailSMSAlertForRequestApproval.as_view()),

    # Dependent on celery and ($ celery -A SSIL_SSO_MS worker -l info) need to be executed
    # TODO: mailsend has been commented for unjustified request(normal user) and date time changed in mail template.
    path('email_sms_alert_for_request_approval_excluding_present/', views.EmailSMSAlertForRequestApprovalExcludingPresent.as_view()),

    # Housekeeper report generation
    path('cws_report_view/', views.CwsReportView.as_view(), name='cws-report-view'),

    #query print api 
    path('query_print/',views.QueryPrint.as_view()),

    # Added By Rupam For get user length or users for testing purpose (attendence cron)
    path('attendance_users/', views.AttendanceUsers.as_view()),

    # User leave report
    path('user_leave_report/', views.UserLeaveReport.as_view(), name='user-leave-report'),
    path('attendance_file_upload_for_sft/', views.AttendanceFileUploadForSFT.as_view()),
    
    # SQL SERVER CONNECTION
    path('test_db_connection/',views.TestDBView.as_view()),

    # ::::::::::::::::: Version 2.0 ( 2020-2021 Attendance Policy ) :::::::::::::::::::#

    # Attendance File Upload for Regular Employee #
    # path('v2/attendance_file_upload/', views.AttendanceFileUploadV2.as_view()),

    # Attendance Request Apply By User #
    path('v2/attendence_approval_request/<pk>/',views.AttendenceApprovalRequestViewV2.as_view()), # user 

    # Attendance Request Approve By Team or HR #
    path('v2/e_task_attendance_approval/',views.ETaskAttendanceApprovalViewV2.as_view()),
    
    # Attendance Leave Grace Balance #
    path('v2/attendance_grace_leave_list_first_modified/', views.AttendanceGraceLeaveListModifiedViewV2.as_view()), # user
    path('v2/attendance_grace_leave_list_for_hr_modified/',views.AttendanceGraceLeaveListForHRModifiedViewV2.as_view()),# hr
    path('v2/attendance_grace_leave_month_wise/', views.AttendanceGraceLeaveMonthWiseView.as_view()),
    
    
    # Attendance Listing #
    path('v2/attendance_daily_list/',views.AttendanceDailyListViewV2.as_view()), # user
    path('v2/attendance_monthly_hr_list/',views.AttendanceMonthlyHRListViewV2.as_view()), # hr
    path('v2/attendance_admin_daily_list/',views.AttendanceAdminDailyListViewV2.as_view()), # team
    path('v2/attendance_leave_approval_list/',views.AttendanceLeaveApprovalListV2.as_view()), # team
    path('v2/e_task_attendance_approval_withoout_grace_list/',views.ETaskAttendanceApprovaWithoutGracelListV2.as_view()),
    path('v2/attendance_admin_summary_list/',views.AttendanceAdminSummaryListViewV2.as_view()), # team
    path('v2/attendance_summary_list/',views.AttendanceSummaryListViewV2.as_view()),
    
    # Attendance Request Document Upload #
    path('v2/attandance_approval_document_upload/',views.AttandanceApprovalDocumentUploadV2.as_view()), # user

    # HR Attendance Report #
    
    path('v2/attendance_new_joiner_report/',views.AttandanceNewJoinerReportViewV2.as_view()), # hr #hrms
    path('v2/attendance_new_joiner_report_export_download/',views.AttandanceNewJoinerReportExportDownloadViewV2.as_view()), # hr #hrms

    path('v2/attendance_sap_hiring_report/',views.AttandanceSAPHiringReportViewV2.as_view()), # hr #hrms
    path('v2/attendance_approval_report/',views.AttendanceApprovalReportViewV2.as_view()), # team
    path('v2/attendance_approval_report_export_download/',views.AttendanceApprovalReportExportDownloadViewV2.as_view()), # team

    # Attendance Database Query and Action #
    path('v2/attendance_database_query/', views.AttendanceDatabaseQueryViewV2.as_view()), # test

    # Corn API (n Days previous Auto Grace/Leave calculation) #
    path('v2/attendance_user_cron_lock_date_before_ndays/', views.AttendanceUserCronLockV2.as_view()), 

    # Yearly Leave Balance Carry Forward Record Creation #
    path('v2/yearly_leave_balance_carry_forward_record_creation', views.YearlyLeaveBalanceCarryForwardRecordCreationV2.as_view()),
    
    # ADVANCE LEAVE #
    path('v2/attendance_advance_leave_add/',views.AttendanceAdvanceLeaveAddV2View.as_view()),
    path('v2/attendance_advance_leave_approval_doc_upload/<pk>/',views.AttendanceAdvanceLeaveApprovalDocUploadV2View.as_view()),
    path('v2/attendance_advance_leave_report/',views.AttendanceAdvanceLeaveReportViewV2.as_view()),
    path('v2/attendance_advance_leave_report_export_download/',views.AttendanceAdvanceLeaveReportExportDownloadViewV2.as_view()),

    path('v2/admin_attendance_advance_leave_pending_list/',views.AdminAttendanceAdvanceLeavePendingListViewV2.as_view()),

    # SPECIAL LEAVE #
    path('v2/attendance_special_leave_add/',views.AttendanceSpecialLeaveAddV2View.as_view()),
    path('v2/attendance_special_leave_list/',views.AttendanceSpecialLeaveListV2View.as_view()),
    
    path('v2/attendance_special_leave_report/',views.AttendanceSpecialLeaveReportV2View.as_view()),
    path('v2/attendance_special_leave_report_export_download/',views.AttendanceSpecialLeaveReportExportDownloadV2View.as_view()),

    path('v2/attendance_special_leave_list_team_hr/',views.AttendanceSpecialLeaveListTeamHrV2View.as_view()),
    path('v2/attendance_special_leave_approval_team_hr/',views.AttendanceSpecialLeaveApprovalTeamHrV2View.as_view()),
    path('v2/attendance_special_leave_approval_doc_upload/<pk>/',views.AttendanceSpecialLeaveApprovalDocUploadV2View.as_view()),

    # API For Cron Mail and SMS Fire #
    path('api_cron_mail_fire/', views.AttendanceCronMailFire.as_view()),
    
    # Work From Home Report #
    path('v2/work_from_home_report/', views.WorkFromHomeReportV2View.as_view()),
    path('v2/work_from_home_report/download/', views.WorkFromHomeReportDownloadV2View.as_view()),

    # Flexi Attendance #
    path('v2/attendance_file_upload/', views.AttendanceFileUploadFlexiHourV2.as_view()),
    # added by Shubhadeep for FRS attendance file upload
    path('v2/attendance_frs_file_upload/', views.AttendanceFRSFileUploadFlexiHourV2Temporary.as_view()),
    path('v2/attendance_frs_file_upload_old/', views.AttendanceFRSFileUploadFlexiHourV2.as_view()),
    # --
    path('v2/flexi_attendance_daily_list/', views.FlexiAttendanceDailyListViewV2.as_view()),
    path('v2/flexi_add_attendance_request/', views.FlexiAddAttendanceRequestViewV2.as_view()),
    path('v2/flexi_attendence_approval_request/<pk>/',views.FlexiAttendenceApprovalRequestViewV2.as_view()),
    path('v2/flexi_attendance_summary_list/',views.FlexiAttendanceSummaryListViewV2.as_view()),

    path('v2/flexi_attendance_grace_leave_list_first_modified/', views.FlexiAttendanceGraceLeaveListModifiedViewV2.as_view()),

    # flexi attendance report
    path('v2/flexi_attendance_approval_report/', views.FlexiAttendanceApprovalReportViewV2.as_view()),  # team
    path('v2/flexi_attendance_approval_report_export_download/',views.FlexiAttendanceApprovalReportExportDownloadViewV2.as_view()),
    path('v2/flexi_attendance_advance_leave_report/', views.FlexiAttendanceAdvanceLeaveReportViewV2.as_view()),
    path('v2/flexi_attendance_advance_leave_report_export_download/',views.FlexiAttendanceAdvanceLeaveReportExportDownloadViewV2.as_view()),
    path('flexi_attendance_conveyance_report_list/', views.FlexiAttendanceConveyanceAfterApprovalListView.as_view()),
    path('flexi_attendance_conveyance_report_list_export_download/',views.FlexiAttendanceConveyanceAfterApprovalListExportDownloadView.as_view()),
    path('v2/flexi_attendance_leave_approval_list/', views.FlexiAttendanceLeaveApprovalListV2.as_view()),  # team
    path('v2/flexi_team_fortnight_attendance/',views.FlexiTeamFortnightAttendance.as_view()),
    
    path('v2/flexi_e_task_attendance_approval_withoout_grace_list/',views.FlexiETaskAttendanceApprovaWithoutGracelListV2.as_view()),
    path('v2/flexi_attendance_admin_daily_list/',views.FlexiAttendanceAdminDailyListViewV2.as_view()), # team
    path('v2/flexi_admin_attendance_advance_leave_pending_list/',views.FlexiAdminAttendanceAdvanceLeavePendingListViewV2.as_view()),
    path('v2/flexi_attendance_admin_summary_list/',views.FlexiAttendanceAdminSummaryListViewV2.as_view()),
    path('v2/flexi_attendance_conveyance_approval_list/',views.FlexiAttendanceConveyanceApprovalListView.as_view()),
    path('v2/flexi_admin_attendance_advance_leave_approval/',views.FlexiAdminAttendanceAdvanceLeaveApprovalView.as_view()),


    ## Attendance automation testing (Rupam Hazra)
    path('v2/attendance_automate/', views.AttendanceAutomateFlexiHourV2.as_view()),


    ## Emergency added for request type P ## As per Change Request Document - Attendance & HRMS -CR-3 | Date : 19-06-2020 | Rupam Hazra ##

    path('v2/attendance_approval_report_for_p_ab/',views.AttendanceApprovalForPresentAbsentReportV2View.as_view()), # team
    path('v2/attendance_approval_report_export_for_p_ab_download/',views.AttendanceApprovalReportExportDownloadForPresentAbsentV2View.as_view()), # team
    path('v2/attendance_file_upload_for_absent/', views.AttendanceFileUploadFlexiHourForAbsentV2.as_view()),

    ## Change Request Document__Attendance & HRMS (Conveyence Management) -CR-2 - V 1.2_Approved | Date: 23-06-2020 | Rupam Hazra ##
    path('attendance_conveyance_configuration_add/', views.AttendanceConveyanceConfigurationAddView.as_view()),
    path('attendance_conveyance_configuration_edit/<pk>/', views.AttendanceConveyanceConfigurationEditView.as_view()),

    path('attendance_conveyance_approval_configuration_add/', views.AttendanceConveyanceApprovalConfigurationAddView.as_view()),
    path('attendance_conveyance_approval_configuration_edit/<pk>/', views.AttendanceConveyanceApprovalConfigurationEditView.as_view()),
    path('attendance_conveyance_approval_configuration_delete/<pk>/', views.AttendanceConveyanceApprovalConfigurationDeleteView.as_view()),

    path('attendance_conveyance_list/', views.AttendanceConveyanceListView.as_view()),
    path('attendance_conveyance_list/details_count/', views.AttendanceConveyanceListDetailsCountView.as_view()),
    path('attendance_conveyance_list/download/', views.AttendanceConveyanceListDownloadView.as_view()),
    
    path('attendance_conveyance_list_for_account/', views.AttendanceConveyanceListForMyAccountView.as_view()),
    path('attendance_conveyance_list_for_account/details_count/', views.AttendanceConveyanceListForMyAccountDetailsCountView.as_view()),
    path('attendance_conveyance_list_for_account/download/', views.AttendanceConveyanceListForMyAccountDownloadView.as_view()),

    path('attendance_conveyance_status_update/', views.AttendanceConveyanceStatusUpdateView.as_view()),
    path('attendance_conveyance_approval_status_update_by_account/', views.AttendanceConveyanceApprovalStatusUpdateByAccountView.as_view()),

    path('attendance_conveyance_edit/<pk>/',views.AttendanceConveyanceUpdateView.as_view()),
    path('attendance_conveyance_add/',views.AttendanceConveyanceAddView.as_view()),

    path('attendance_conveyance_doc_upload/',views.AttendanceConveyanceDocAddView.as_view()),

    path('attendance_conveyance_payment_update/', views.AttendanceConveyancePaymentUpdateView.as_view()),

    path('attendance_conveyance_all_count/',views.AttendanceConveyanceALLCountView.as_view()),

    ## Change Request HRMS_Conveyance CR-5.0 doc | Date: 16-09-2020 | Rupam Hazra ##

    # Travel Mode,Price
    path('travel_mode/add/', views.TravelModeAddView.as_view()),
    path('travel_mode/edit/<pk>/', views.TravelModeEditView.as_view()),
    path('attendance_conveyance_configuration/details/', views.AttendanceConveyanceConfigurationDetailsView.as_view()),


    #attendance auto approval status
    path('attendance/attendance_approval_status/edit/<pk>/', views.AttendanceAutoApprovalStatusEditView.as_view()),

    ##document raw data upload
    path('v2/attendance_frs_file_raw_data_upload/', views.AttendanceFRSFileAndRawDataUploadFlexiHourV2.as_view()),
    path('v2/attendance_update_with_file_raw_data/', views.AttendanceFRSFileAndRawDataUpdateFlexiHourV2.as_view()),

    ##Attendance FRS Raw Data
    path('attendance_frs_raw_data/add/', views.AttendanceFRSRawDataAddView.as_view()),
    path('attendance_frs_raw_data/edit/<pk>/', views.AttendanceFRSRawDataEditView.as_view()),

    



    # Leave calculation upto till date
    path('attendance/leave_grace_calculation/download/', views.AttendanceGraceLeaveCalculationDwonload.as_view()), # all user
]