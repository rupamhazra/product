from django.urls import path
from hrms import views
from django.conf.urls import url, include
from rest_framework.authtoken import views as rest_framework_views


urlpatterns = [

#:::::::::::::::::::::: HRMS BENEFITS PROVIDED:::::::::::::::::::::::::::#
path('hrms_benefits_provided_add/', views.BenefitsProvidedAddView.as_view()),
path('hrms_benefits_provided_edit/<pk>/', views.BenefitsProvidedEditView.as_view()),
path('hrms_benefits_provided_delete/<pk>/', views.BenefitsProvidedDeleteView.as_view()),

#:::::::::::::::::::::: HRMS QUALIFICATION MASTER:::::::::::::::::::::::::::#
path('qualification_master_add/', views.QualificationMasterAddView.as_view()),
path('qualification_master_edit/<pk>/', views.QualificationMasterEditView.as_view()),
path('qualification_master_delete/<pk>/', views.QualificationMasterDeleteView.as_view()),

#:::::::::::::::::::::: HRMS EMPLOYEE:::::::::::::::::::::::::::#
# path('employee_add/',views.EmployeeAddView.as_view()),
# path('employee_edit/<pk>/',views.EmployeeEditView.as_view()),
# path('employee_list/',views.EmployeeListView.as_view()),
path('employee_list_export_download/',views.EmployeeListExportDownloadView.as_view()),

path('employee_list_for_active_users/',views.EmployeeActiveUserListView.as_view()),

path('employee_list_without_details/',views.EmployeeListWithoutDetailsView.as_view()),
path('employee_list_wo_pagination/',views.EmployeeListWOPaginationView.as_view()),

path('employee_list_for_hr/',views.EmployeeListForHrView.as_view()),
path('employee_list_for_hr_export_download/',views.EmployeeListForHrExportDownloadView.as_view()),

path('employee_lock_unlock/<pk>/', views.EmployeeActiveInactiveUserView.as_view()),

path('hrms_employee_document_add/',views.DocumentAddView.as_view()),
path('hrms_employee_document_delete/<pk>/',views.DocumentDeleteView.as_view()),

path('hrms_employee_profile_document_add/',views.HrmsEmployeeProfileDocumentAddView.as_view()),
path('hrms_employee_profile_document_delete/<pk>/',views.HrmsEmployeeProfileDocumentDeleteView.as_view()),

path('hrms_employee_academic_qualification_add/',views.HrmsEmployeeAcademicQualificationAddView.as_view()),
path('hrms_employee_academic_qualification_delete/<pk>/',views.HrmsEmployeeAcademicQualificationDeleteView.as_view()),

path('hrms_employee_academic_qualification_document_add/',views.HrmsEmployeeAcademicQualificationDocumentAddView.as_view()),
path('hrms_employee_academic_qualification_document_delete/<pk>/',views.HrmsEmployeeAcademicQualificationDocumentDeleteView.as_view()),

path('employee_add_by_csv_or_excel/',views.EmployeeAddByCSVorExcelView.as_view()),
path('employee_details_update_through_sap_personnel_no/',views.EmployeeDetailsUpdateThroughSAPPersonnelNoView.as_view()),

#:::::::::::::::::::::: HRMS NEW REQUIREMENT:::::::::::::::::::::::::::#
path('hrms_new_requirement/',views.HrmsNewRequirementAddView.as_view()),

#:::::::::::::::::::::: HRMS INTERVIEW TYPE:::::::::::::::::::::::::::#
path('hrms_interview_type_add/', views.InterviewTypeAddView.as_view()),
path('hrms_interview_type_edit/<pk>/', views.InterviewTypeEditView.as_view()),
path('hrms_interview_type_delete/<pk>/', views.InterviewTypeDeleteView.as_view()),

#:::::::::::::::::::::: HRMS INTERVIEW LEVEL:::::::::::::::::::::::::::#
path('hrms_interview_level_add/', views.InterviewLevelAddView.as_view()),
path('hrms_interview_level_edit/<pk>/', views.InterviewLevelEditView.as_view()),
path('hrms_interview_level_delete/<pk>/', views.InterviewLevelDeleteView.as_view()),

#:::::::::::::::::::::: HRMS SCHEDULE INTERVIEW :::::::::::::::::::::::::::#
path('schedule_interview_add/',views.ScheduleInterviewAddView.as_view()),
path('reschedule_interview_add/',views.RescheduleInterviewAddView.as_view()),
path('interview_status_add/<pk>/',views.InterviewStatusAddView.as_view()),
path('interview_status_list/',views.InterviewStatusListView.as_view()),
path('candidature_update_data_edit/<pk>/', views.CandidatureUpdateEditView.as_view()),
path('candidature_level_approval/<pk>/', views.CandidatureApproveEditView.as_view()),
path('open_and_closed_requirement_list/',views.OpenAndClosedRequirementListView.as_view()),
path('upcoming_and_interview_history_list/',views.UpcomingAndInterviewHistoryListView.as_view()),


### FOR NEW RULES & REGULATION IN ATTENDENCE SYSTEM FOR FINANCIAL YEAR [2020-2021] ######

# Employee #
path('employee_add/',views.EmployeeAddV2View.as_view()),
path('employee_list/',views.EmployeeListViewV2.as_view()),
path('employee_edit/<pk>/',views.EmployeeEditViewV2.as_view()),

path('v2/employee_leave_allocation_on_first_day_of_year_start/',views.EmployeeLeaveAllocateV2View.as_view()),

# Report #
path('v2/employee_list_for_inactive_users/',views.EmployeeInactiveUserListView.as_view()),

#active user

path('v2/employee_list_for_active_users/',views.EmployeeActiveUserListV2View.as_view()),

path('v2/employee_list_for_active_user/download/', views.EmployeeActiveUserListDownload.as_view()),

path('v2/employee_view_password_verification/', views.EmployeeViewPasswordVerification.as_view()),

path('v2/employee_unapplied_attendance_list/', views.UnAppliedAttendanceListView.as_view()),
path('v2/employee_unapproved_attendance_list/', views.UnAttendedAttendanceListView.as_view()),

path('v2/employee_unapplied_attendance_report/download/', views.UnAppliedAttendanceReportDownloadView.as_view()),
path('v2/employee_unapproved_attendance_report/download/', views.UnAttendedAttendanceReportDownloadView.as_view()),

#flexi user #

path('v2/flexi_employee_list_without_details/',views.FlexiEmployeeListWithoutDetailsView.as_view()),



#CR-1.0
path('v2/employee_list_under_resigned_rh/',views.EmployeeListUnderResignedReportingHeadV2View.as_view()),
path('v2/employee_list_under_resigned_rh_export_download/',views.EmployeeListUnderResignedReportingHeadDownloadV2View.as_view()),
path('v2/resigned_rh_details/<pk>/', views.ResignedRhDetailView.as_view()),
path('v2/employee_list_for_choseing_new_rh/', views.EmployeeListForNewReportingHeadV2View.as_view()),
path('v2/chnge_rh_for_selected_user/', views.ReportingHeadChangeV2View.as_view()),
path('v2/list_of_reportees_under_rh/',views.ListOfReporteesView.as_view()),

# leave change on the basis of salary type(postman use)
path('employee_lave_allocation_modify/', views.EmployeeLeaveAllcationModify.as_view()),

# path('hrms/three_month_probation_form/employee_details/', views.EmployeeDetailsForProbationAddView.as_view()),
# path('hrms/three_month_probation_form/add/', views.ProbationThreeMonthsAddView.as_view()),
path('hrms/three_month_probation_submission_pending/list/', views.PendingThreeMonthsProbatinEmployeeListV2View.as_view()),
path('hrms/three_month_probation_pending_reminder_by_hr/', views.PendingThreeMonthSubmissionReminderFromHr.as_view()),
path('hrms/three_month_pending_probation_form/add/<pk>/', views.PendingProbationThreeMonthsAddView.as_view()),
path('hrms/three_month_pending_probation_review_form/add/<pk>/', views.PendingProbationThreeMonthsReviewAddView.as_view()),
path('hrms/three_month_probation_review_submission_pending/list/', views.PendingThreeMonthsProbatinReviewListV2View.as_view()),
path('hrms/three_month_probation_review_pending_reminder_by_hr/', views.PendingThreeMonthReviewSubmissionReminderFromHr.as_view()),
path('hrms/three_month_probation_review_reminder_job/', views.EmployeeProbationReminder.as_view()),
path('hrms/three_month_confirmation_report/list/', views.ThreeMonthsProbationConfirmationReportView.as_view()),

path('hrms/five_month_probation_submission_pending/list/', views.PendingFiveMonthsProbationEmployeeListView.as_view()),
path('hrms/five_month_probation_pending_reminder_by_hr/', views.PendingFiveMonthSubmissionReminderFromHr.as_view()),
path('hrms/five_month_pending_probation_form/add/<pk>/', views.PendingFiveMonthsProbationAddView.as_view()),
path('hrms/five_month_pending_probation_review_form/add/<pk>/', views.PendingFiveMonthsProbationReviewAddView.as_view()),
path('hrms/five_month_probation_review_submission_pending/list/', views.PendingFiveMonthsProbatinReviewListView.as_view()),
path('hrms/five_month_probation_review_pending_reminder_by_hr/', views.PendingFiveMonthReviewSubmissionReminderFromHr.as_view()),
path('hrms/five_month_probation_review_reminder_job/', views.EmployeeFiveMonthsProbationReminder.as_view()),
path('hrms/five_month_confirmation_report/list/', views.FiveMonthsProbationConfirmationReportView.as_view()),
path('hrms/five_month_confirmation_pending_report/list/', views.FiveMonthsProbationPendingConfirmationListView.as_view()),
path('hrms/confirm_employee/<pk>/', views.ProbationConfirmEmployeeView.as_view()),


# api for employee rejoin
path('hrms/employee-rejoin_suggestion/list/', views.EmployeeRejoinSuggestionListView.as_view()),
path('hrms/rejoin_employee/details/', views.EmployeeRejoinAddView.as_view()),

# api for employee transfer
path('hrms/employee_transfer/<pk>/', views.EmployeeTransferView.as_view()),
path('hrms/employee_transfer_list/', views.TransferHistoryListView.as_view()),

#payslip download
# EmployeePaySlipDownloadView
path('hrms/employee_payslip/download/', views.EmployeePaySlipDownloadView.as_view()),

# New version of employee_list_without_details [Added by Rupam]
path('v2/employee_list_without_details/',views.EmployeeListWithoutDetailsV2View.as_view()),

# Intercom
path('hrms/intercom/upload/excel/',views.IntercomUploadExcelView.as_view()),
path('hrms/intercom/add/',views.IntercomAddView.as_view()),
path('hrms/intercom/edit/<pk>/',views.IntercomEditView.as_view()),

### pre_joining_onset_form###

path('prejoining_process_onset_form/add/', views.PreJoiningOnsetFormView.as_view()),
path('pre_joining_list/', views.PreJoiningListView.as_view()),
path('pre_joining_list_update/<pk>/', views.PreJoiningUpdateView.as_view()),
path('pre_joining_resource/add/', views.PreJoinineeResourceAddView.as_view()),
path('pre_joining_resource_allocation_reminder_job/', views.PreJoineeResourceAllocationReminder.as_view()),

path('employee_mediclaim_add/', views.EmployeeMediclaimAddView.as_view()),
path('employee_mediclaim_list/', views.EmployeeMediclaimListView.as_view()),
path('employee_mediclaim_report/download/', views.EmployeeMediclaimReportDownloadView.as_view()),
path('employee_marital_status_check/', views.EmployeeMaritalStatusCheck.as_view()),
path('employee_mediclaim_details/', views.EmployeeMediclaimDetailsView.as_view()),
path('employee_mediclaim_retrive_update/<pk>/', views.EmployeeMediclaimRetriveUpdateView.as_view()),
path('enable_mediclaim_edit/', views.EmployeeMediclaimEnableEditView.as_view()),

]