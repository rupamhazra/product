from django.urls import path

from etask import views

# from django.conf.urls import url, include
# from rest_framework.authtoken import views as rest_framework_views

urlpatterns = [
    # ::::::::::::::::::::::::: TASK ADD ::::::::::::::::::::::::::: #
    # path('etask_type_add/',views.EtaskTypeAddView.as_view()),
    path('etask_task_add/', views.EtaskTaskAddView.as_view()),
    path('etask_task_details/<pk>/', views.EtaskTaskRepostView.as_view()),
    path('etask_task_edit/<pk>/', views.EtaskTaskEditView.as_view()),
    path('etask_task_delete/<pk>/', views.EtaskTaskDeleteView.as_view()),
    path('etask_parent_task_list/', views.EtaskParentTaskListView.as_view()),
    path('etask_my_task_list/',views.EtaskMyTaskListView.as_view()),  ## Modified by manas ##
    path('etask_completed_task_list/',views.EtaskCompletedTaskListView.as_view()), ## Modified by manas ##
    path('etask_closed_task_list/',views.EtaskClosedTaskListView.as_view()),  ## Modified by manas ##
    path('etask_overdue_task_list/',views.EtaskOverdueTaskListView.as_view()), ## Modified by manas ##
    path('etask_task_list/',views.EtasktaskListView.as_view()),
    path('etask_task_status_list/',views.EtaskTaskStatusListView.as_view()),
    path('e_task_all_task_list/',views.ETaskAllTasklist.as_view()),#Modified by koushik##
    path('e_task_upcoming_completion_list/',views.ETaskUpcomingCompletionListView.as_view()), ## Created by manas ##
    path('etask_task_cc_list/',views.EtaskTaskCCListview.as_view()), ## Created by manas ##
    path('etask_task_transffered_list/',views.EtaskTaskTransferredListview.as_view()), ## Created by manas ##
    path('e_task_task_complete/<pk>/',views.EtaskTaskCompleteView.as_view()), ## Created by manas ##
    path('etask_my_task_todays_planner_list/',views.EtaskMyTaskTodaysPlannerListView.as_view()),  ## Modified by manas ##   
    path('etask_end_date_extension_request/<pk>/',views.EtaskEndDateExtensionRequestView.as_view()),
    path('etask_extensions_list_for_rh_or_hod/',views.EtaskExtensionsListView.as_view()),   
    path('etask_extensions_reject/<pk>/',views.EtaskExtensionsRejectView.as_view()),  
    path('etask_task_date_extended/<pk>/',views.EtaskTaskDateExtendedView.as_view()),  ## Modified by manas ##        
    path('etask_task_date_extended_with_delay/<pk>/',views.EtaskTaskDateExtendedWithDelayView.as_view()),  ## Modified by manas ##    
    path('etask_task_reopen_and_extend_with_delay/<pk>/',views.EtaskTaskReopenAndExtendWithDelayView.as_view()),
    path('etask_task_start_date_shift/<pk>/',views.EtaskTaskStartDateShiftView.as_view()),    
    path('etask_all_type_task_count/',views.EtaskAllTypeTaskCountView.as_view()),  ## Modified by manas ##        
    path('etask_getdetails_list/',views.ETaskGetDetailForCommentListView.as_view()),

    #::::::::::::::::::::::::: TASK COMMENTS:::::::::::::::::::::::::::#
    path('e_task_comments/',views.ETaskCommentsView.as_view()), ## Created by manas ##
    path('e_task_comments_viewers/',views.ETaskCommentsViewersView.as_view()),
    path('e_task_unread_comments/<user_id>/',views.ETaskUnreadCommentsView.as_view()),
    path('e_task_comments_advance_attachment_add/',views.ETaskCommentsAdvanceAttachmentAddView.as_view()), ## Created by manas ##
    path('e_task_comments_list/',views.EtasCommentsListView.as_view()), ## Created by manas ##
      
    #::::::::::::::::::::::::: Followup COMMENTS:::::::::::::::::::::::::::#
    path('e_task_followup_comments/',views.ETaskFollowupCommentsView.as_view()), ## Created by manas ##
    path('e_task_followup_comments_advance_attachment_add/',views.ETaskFollowupCommentsAdvanceAttachmentAddView.as_view()), ## Created by manas ##
    path('e_task_followup_comments_list/',views.EtasFollowupCommentsListView.as_view()), ## Created by manas ##

    #::::::::::::::::::::::::: TASK SUB ASSIGN:::::::::::::::::::::::::::#
    path('e_task_sub_assign/<pk>/',views.ETaskSubAssignView.as_view()), ## Modified by manas ##
    
    #::::::::::::::::::::::::: Follow UP:::::::::::::::::::::::::::#
    path('e_task_add_new_follow_up/',views.EtaskAddFollowUpView.as_view()),
    path('e_task_follow_up_list/<user_id>/',views.EtaskFollowUpListView.as_view()),
    path('e_task_todays_follow_up_list/<user_id>/',views.EtaskTodaysFollowUpListView.as_view()),
    path('e_task_upcoming_follow_up_list/<user_id>/',views.EtaskUpcomingFollowUpListView.as_view()),
    path('e_task_overdue_follow_up_list/<user_id>/',views.EtaskOverdueFollowUpListView.as_view()),
    path('e_task_follow_up_complete/<pk>/',views.EtaskFollowUpCompleteView.as_view()),
    path('v2/e_task_multi_follow_up_complete/',views.EtaskMultiFollowUpCompleteView.as_view()),
    path('e_task_follow_up_delete/<pk>/',views.EtaskFollowUpDeleteView.as_view()),
    path('e_task_follow_up_edit/<pk>/',views.EtaskFollowUpEditView.as_view()),
    path('e_task_follow_up_reschedule/<pk>/',views.EtaskFollowUpRescheduleView.as_view()),
    path('v2/e_task_multi_follow_up_reschedule/',views.EtaskMultiFollowUpRescheduleView.as_view()),
    path('e_task_assign_to_list/',views.ETaskAssignToListView.as_view()),
    path('e_task_sub_assign_to_list/',views.ETaskSubAssignToListView.as_view()),

    #:::::::::::::::::::::::: Send Mail For ETask Comments ::::::::::::::::::::::::::#
    # path('e_task_all_mail_one_time_send/',views.ETaskAllMailOneTimeSendView.as_view()),

    #::::::::::::::::::::::::: APPOINTMENTS COMMENTS:::::::::::::::::::::::::::#
    path('e_task_appointment_add/',views.ETaskAppointmentAddView.as_view()),
    path('e_task_appointment_edit/<pk>/',views.ETaskAppointmentUpdateView.as_view()),
    path('e_task_appointment_comments/',views.ETaskAppointmentCommentsView.as_view()), ## Created by manas ##
    path('e_task_appointment_comments_advance_attachment_add/',views.ETaskAppointmentCommentsAdvanceAttachmentAddView.as_view()), ## Created by manas ##
    path('e_task_appointment_comments_list/',views.EtaskAppointmentCommentsListView.as_view()), ## Created by manas ##
    path('e_task_appointment_calander/',views.ETaskAppointmentCalanderView.as_view()),
    path('e_task_appointment_calander_weekly/',views.ETaskAppointmentCalanderWeeklyView.as_view()),
    path('e_task_allcomment/',views.ETaskAllCommentListView.as_view()),
    path('e_task_allcomment_documents/',views.ETaskAllCommentDocumentListView.as_view()),
    path('e_task_appointment_cancel/<pk>/',views.ETaskAppointmentCancelView.as_view()),

    #::::::::::::::::::::::::: REPORTING :::::::::::::::::::::::::::#
    path('e_task_reports/',views.ETaskReportsView.as_view()),#::Created by koushik::#
    path('etask_upcoming_reporting_list/',views.EtaskUpcommingReportingListView.as_view()), ## Created by manas ##
    path('etask_reporting_date_reported/<pk>/',views.EtaskReportingDateReportedView.as_view()), ## Created by manas ##
    path('etask_reporting_date_shift/',views.EtaskReportingDateShiftView.as_view()), ## Created by manas ##
    
    #::::::::::::::::::::::::: ADMIN REPORT :::::::::::::::::::::::::::#
    path('e_task_admin_task_report/',views.ETaskAdminTaskReportView.as_view()), #Created by koushik##
    path('e_task_admin_appointment_report/',views.ETaskAdminAppointmentReportView.as_view()), #Created by koushik##

    #::::::::::::::::::::::::: TEAM :::::::::::::::::::::::::::#
    path('e_task_team_ongoing_task/',views.ETaskTeamOngoingTaskView.as_view()),#Created by koushik## ## Modfied By Manas Paul##
    path('e_task_team_completed_task/',views.ETaskTeamCompletedTaskView.as_view()),#Created by koushik##
    path('e_task_team_closed_task/',views.ETaskTeamClosedTaskView.as_view()),#Created by koushik##
    path('e_task_closures_task_list/',views.ETaskClosuresTaskListView.as_view()),
    path('e_task_team_overdue_task/',views.ETaskTeamOverdueTaskView.as_view()),#Created by koushik##
    path('e_task_task_close/<pk>/',views.EtaskTaskCloseView.as_view()), ## Created by koushik ##
    path('e_task_mass_task_close/',views.ETaskMassTaskCloseView.as_view()),

    path('employee_list_without_details_for_e_task/',views.EmployeeListWithoutDetailsForETaskView.as_view()),

    #::::::::::::::::::::::: TODAYS PLANNING :::::::::::::::::::::::#
    path('e_task_today_appointment_list/',views.EtaskTodayAppointmentListView.as_view()),
    path('e_task_upcoming_appointment_list/',views.EtaskUpcomingAppointmentListView.as_view()),

    #::::::::::::::::UPCOMING TASK ALONG WITH TEAM:::::::::::::::::::::::::::::::::::::#
    path('upcoming_task_along_with_team/',views.UpcomingTaskAlongWithTeamView.as_view()),
    path('upcoming_task_per_user/<user_id>/',views.UpcomingTaskPerUserView.as_view()),

    path('upcoming_task_reporting_along_with_team/',views.UpcomingTaskReportingAlongWithTeamView.as_view()),
    path('upcoming_task_reporting_per_user/<user_id>/',views.UpcomingTaskReportingPerUserView.as_view()),
    
    #::::::::::::::::TODAYS TASK ALONG WITH TEAM:::::::::::::::::::::::::::::::::::::#
    path('todays_task_along_with_team/',views.TodaysTaskAlongWithTeamView.as_view()),
    path('todays_task_reporting_along_with_team/',views.TodaysTaskReportingAlongWithTeamView.as_view()),

    #::::::::::::::::DEFAULT REPORTING DATES:::::::::::::::::::::::::::::::::::::#
    path('e_task_default_reporting_dates_add/',views.ETaskDefaultReportingDatesView.as_view()),
    path('e_task_another_default_reporting_dates_add/',views.ETaskAnotherDefaultReportingDatesView.as_view()),
    path('e_task_default_reporting_dates_update/<pk>/',views.ETaskDefaultReportingDatesUpdateView.as_view()),
    path('e_task_default_reporting_dates_delete/<pk>/',views.ETaskDefaultReportingDatesDeleteView.as_view()),

    #:::::::::::::::::::::::::::::::::::::::::::  N E W  ::::::::::::::::::::::::::::::::::::::::::::#
    #================================================================================================#
    #:::::::::::::::::::::::::::::::::::::: TASK LIST -NEW ::::::::::::::::::::::::::::::::::::::::::#
    path('today_task_details_per_user/<user_id>/',views.TodayTaskDetailsPerUserView.as_view()),
    path('upcoming_task_details_per_user/<user_id>/',views.UpcomingTaskDetailsPerUserView.as_view()),
    path('overdue_task_details_per_user/<user_id>/',views.OverdueTaskDetailsPerUserView.as_view()),
    path('closed_task_details_per_user/<user_id>/',views.ClosedTaskDetailsPerUserView.as_view()),
    path('e_task_todays_planner_count/<user_id>/',views.ETaskTodaysPlannerCountView.as_view()),

    #:::::::::::::::::::::::::::::::::::::: REPORTING ::::::::::::::::::::::::::::::::::::::::::::::::#
    path('today_reporting_details_per_user/<user_id>/',views.TodayReportingDetailsPerUserView.as_view()),
    path('upcoming_reporting_details_per_user/<user_id>/',views.UpcomingReportingDetailsPerUserView.as_view()),
    path('overdue_reporting_details_per_user/<user_id>/',views.OverdueReportingDetailsPerUserView.as_view()),
    path('today_reporting_mark_date_reported/<pk>/',views.TodayReportingMarkDateReportedView.as_view()),

    #:::::::::::::::::::::::::::::::::::::: APPOINMENT ::::::::::::::::::::::::::::::::::::::::::::::::#
    path('today_appointment_details_per_user/<user_id>/',views.TodayAppointmenDetailsPerUserView.as_view()),
    path('upcoming_appointment_details_per_user/<user_id>/',views.UpcomingAppointmenDetailsPerUserView.as_view()),
    path('overdue_appointment_details_per_user/<user_id>/',views.OverdueAppointmenDetailsPerUserView.as_view()),
    path('closed_appointment_details_per_user/<user_id>/',views.ClosedAppointmenDetailsPerUserView.as_view()),
    path('today_appoinment_mark_completed/<pk>/',views.TodayAppoinmentMarkCompletedView.as_view()),

    #:::::::::::::::::::::::::::::::::::::: TASK TRANSFER ::::::::::::::::::::::::::::::::::::::::::::::::#
    path('e_task_mass_task_transfer/',views.ETaskMassTaskTransferView.as_view()),
    path('e_task_team_transfer_tasks_list/<user_id>/',views.ETaskTeamTransferTasksListView.as_view()),
    path('e_task_team_tasks_transferred_list/',views.ETaskTeamTasksTransferredListView.as_view()),

    #::::::::::::::::::::::::::::::::::::::::::::: COUNT ::::::::::::::::::::::::::::::::::::::::::::::::::::::#
    path('today_count_details_per_user/<user_id>/',views.TodayCountDetailsPerUserView.as_view()),
    path('upcoming_count_details_per_user/<user_id>/',views.UpcomingCountDetailsPerUserView.as_view()),
    path('overdue_count_details_per_user/<user_id>/',views.OverDueCountDetailsPerUserView.as_view()),
    path('closed_count_details_per_user/<user_id>/',views.ClosedCountDetailsPerUserView.as_view()),
    path('dashboard_count_details/',views.DashboardCountDetailsView.as_view()),

    #::::::::::::::::::::::::::::::::::::::::::::: PRINT PLANNER ::::::::::::::::::::::::::::::::::::::::::::::::::::::#
    path('today_tomorrow_upcoming_planner/',views.TodayTomorrowUpcomingPlannerView.as_view()),

    #::::::::::::::::::::::: daily sheet :::::::::::::::::::::::::::::#
    path('dailysheet_task_add/', views.DailysheetTaskAddView.as_view()),
    path('dailysheet_list/', views.DailysheetTaskListView.as_view()),
    path('dailysheet_edit/<pk>/', views.DailySheetEditView.as_view()),
    path('dailysheet_delete/<pk>/', views.DailySheetDeleteView.as_view()),


    # :::::::::::::::::::::::::::::::::: Etask Changes(version 2) ::::::::::::::::::::::::::::::::::: #
    # Etask Database Query and Action #
    path('v2/etask_database_query/', views.EtaskDatabaseQueryView.as_view()), # test
    
    ### Etask - profile job cron ###
    path('etask_task_profile_job_add_cron/',views.EtaskTaskProfileJobCronAddView.as_view()),
    
    # Count #
    path('v2/dashboard_count_details/',views.DashboardCountDetailsViewV2.as_view()), 

    # Etask CURD #
    path('v2/etask_task_add/',views.EtaskTaskAddViewV2.as_view()),
    path('v2/etask_task_edit/<pk>/',views.EtaskTaskEditViewV2.as_view()),
    path('v2/etask_task_delete/<pk>/',views.EtaskTaskDeleteViewV2.as_view()),
    path('v2/e_task_sub_assign/<pk>/',views.ETaskSubAssignViewV2.as_view()),

    # Etask Action #
    path('v2/etask_task_start_date_shift/<pk>/',views.EtaskTaskStartDateShiftViewV2.as_view()),
    path('v2/etask_mass_start_date_shift/',views.EtaskMassStartDateShiftView.as_view()),
    path('v2/e_task_task_complete/<pk>/',views.EtaskTaskCompleteViewV2.as_view()),
    path('v2/e_task_multiple_task_complete/',views.EtaskMultipleTaskCompleteViewV2.as_view()),
    path('v2/etask_end_date_extension_request/<pk>/',views.EtaskEndDateExtensionRequestViewV2.as_view()),
    #path('v2/etask_multiple_end_date_extension_request/',views.EtaskMultipleEndDateExtensionRequestViewV2.as_view()),
    path('v2/etask_multi_end_date_extension_request/',views.EtaskMultiEndDateExtensionRequestViewV2.as_view()),
    path('v2/etask_task_date_extended/<pk>/',views.EtaskTaskDateExtendedViewV2.as_view()),
    path('v2/etask_mass_date_extended/',views.EtaskMassDateExtendedView.as_view()),
    path('v2/etask_task_date_extended_with_delay/<pk>/',views.EtaskTaskDateExtendedWithDelayViewV2.as_view()),
    path('v2/etask_task_reopen_and_extend_with_delay/<pk>/',views.EtaskTaskReopenAndExtendWithDelayViewV2.as_view()),
    path('v2/etask_extensions_reject/<pk>/',views.EtaskExtensionsRejectViewV2.as_view()),
    path('v2/e_task_task_close/<pk>/',views.EtaskTaskCloseViewV2.as_view()),
    path('v2/e_task_mass_task_close/',views.ETaskMassTaskCloseViewV2.as_view()),

    # Task Transfer #
    path('v2/e_task_ownership_transfer/',views.ETaskOwnershipTransferView.as_view()),
    path('v2/e_task_team_ownership_transfer_tasks_list/',views.ETaskTeamOwnershipTransferTaskListView.as_view()),
    path('v2/e_task_team_ownership_transferred_list/',views.ETaskTeamOwnershipTransferredListView.as_view()),
    path('v2/e_task_team_transfer_tasks_list/',views.ETaskTeamTransferTasksListViewV2.as_view()),
    path('v2/e_task_team_tasks_transferred_list/',views.ETaskTeamTasksTransferredListViewV2.as_view()),
    path('v2/e_task_mass_task_transfer/',views.ETaskMassTaskTransferViewV2.as_view()),

    # Reporting Date #
    path('v2/e_task_default_reporting_dates_add/',views.ETaskDefaultReportingDatesViewV2.as_view()),
    path('v2/e_task_default_reporting_dates_update/<pk>/',views.ETaskDefaultReportingDatesUpdateViewV2.as_view()),
    path('v2/etask_reporting_date_add/',views.EtaskReportingDateAddView.as_view()),
    path('v2/etask_mass_reporting_date_add/',views.EtaskMassReportingDateAddView.as_view()),
    path('v2/etask_mark_add_reporting_date/<pk>/',views.EtaskReportingDateReportedViewV2.as_view()),
    path('v2/etask_mass_mark_add_reporting_date/',views.EtaskMassMarkAddReportingDateView.as_view()),
    
    # Etask Comments #
    path('v2/e_task_comments_list/',views.EtasCommentsListViewV2.as_view()),
    path('v2/e_task_comments/',views.ETaskCommentsViewV2.as_view()),
    # path('v2/e_task_comments/',views.ETaskCommentsViewV2.as_view()),
    path('v2/e_task_mass_comments_viewers/',views.ETaskMassCommentsViewersView.as_view()),

    # Etask Appointment #
    path('v2/e_task_appointment_add/',views.ETaskAppointmentAddViewV2.as_view()),
    path('v2/e_task_appointment_edit/<pk>/',views.ETaskAppointmentUpdateViewV2.as_view()),
    path('v2/e_task_appointment_cancel/<pk>/',views.ETaskAppointmentCancelViewV2.as_view()),

    # Etask Follow Up #
    path('v2/e_task_add_new_follow_up/',views.EtaskAddFollowUpViewV2.as_view()),

    # Detail View #
    path('v2/etask_task_details/<pk>/',views.EtaskTaskRepostViewV2.as_view()),
    path('v2/etask_follow_up_details/<pk>/',views.EtaskFollowUpDetailsView.as_view()),
    path('v2/etask_appointment_details/<pk>/',views.EtaskAppointmentDetailsView.as_view()),

    # User List #
    path('v2/users_under_reporting_head/',views.UsersUnderReportingHeadView.as_view()),
    path('v2/users_reporting_head/',views.UsersReportingHeadView.as_view()),
    path('v2/users_for_etask_filter/',views.UsersForEtaskFilterView.as_view()),
    path('v2/users_for_cc_filter/',views.UsersForCCFilterView.as_view()),

    # Todays Planner #
    path('v2/today_task_details_per_user/',views.TodayTaskDetailsPerUserViewV2.as_view()),
    path('v2/today_priority_task_details_per_user/',views.TodayPriorityTaskDetailsPerUserViewV2.as_view()),
    path('v2/today_reporting_details_per_user/',views.TodayReportingDetailsPerUserViewV2.as_view()),
    path('v2/overdue_reporting_list/',views.OverdueReportingListView.as_view()),
    path('v2/todays_reporting_list/',views.TodaysReportingListView.as_view()),
    path('v2/e_task_todays_follow_up_list/',views.EtaskTodaysFollowUpListViewV2.as_view()),
    path('v2/today_appointment_details_per_user/',views.TodayAppointmenDetailsPerUserViewV2.as_view()),
    path('v2/etask_extensions_list_for_rh_or_hod/',views.EtaskExtensionsListViewV2.as_view()),
    path('v2/e_task_closures_task_list/',views.ETaskClosuresTaskListViewV2.as_view()),
    path('v2/e_task_unread_comments/',views.ETaskUnreadCommentsViewV2.as_view()),
    # path('v2/today_task_history_per_user/',views.TodayTaskHistoryPerUserView.as_view()), # History **Yet to be completed

    # ::::: Todays Planner DOWNLOAD ::::: #
    path('v2/etask_reporting_list_download/',views.EtaskReportingListDownloadView.as_view()),
    path('v2/today_task_details_per_user_download/',views.TodayTaskDetailsPerUserDownloadViewV2.as_view()),
    path('v2/today_priority_task_details_per_user_download/',views.TodayPriorityTaskDetailsPerUserDownloadViewV2.as_view()),
    path('v2/today_reporting_details_per_user_download/',views.TodayReportingDetailsPerUserDownloadViewV2.as_view()),
    path('v2/e_task_todays_follow_up_list_download/',views.EtaskTodaysFollowUpListDownloadViewV2.as_view()),
    path('v2/today_appointment_details_per_user_download/',views.TodayAppointmenDetailsPerUserDownloadViewV2.as_view()),
    path('v2/etask_extensions_list_for_rh_or_hod_download/',views.EtaskExtensionsListDownloadViewV2.as_view()),
    path('v2/e_task_closures_task_list_download/',views.ETaskClosuresTaskListDownloadViewV2.as_view()),
    path('v2/e_task_unread_comments_download/',views.ETaskUnreadCommentsDownloadViewV2.as_view()),

    # Upcomming Task #
    path('v2/upcoming_reporting_list/',views.UpcomingReportingListView.as_view()),
    path('v2/upcoming_task_details_per_user/',views.UpcomingTaskDetailsPerUserViewV2.as_view()),
    path('v2/upcoming_reporting_details_per_user/',views.UpcomingReportingDetailsPerUserViewV2.as_view()),
    path('v2/e_task_upcoming_follow_up_list/',views.EtaskUpcomingFollowUpListViewV2.as_view()),
    path('v2/upcoming_appointment_details_per_user/',views.UpcomingAppointmenDetailsPerUserViewV2.as_view()),

    # ::::: Upcoming Task DOWNLOAD ::::: #
    path('v2/upcoming_task_details_per_user_download/',views.UpcomingTaskDetailsPerUserDownloadViewV2.as_view()),
    path('v2/upcoming_reporting_details_per_user_download/',views.UpcomingReportingDetailsPerUserDownloadViewV2.as_view()),
    path('v2/e_task_upcoming_follow_up_list_download/',views.EtaskUpcomingFollowUpListDownloadViewV2.as_view()),
    path('v2/upcoming_appointment_details_per_user_download/',views.UpcomingAppointmenDetailsPerUserDownloadViewV2.as_view()),

    # Closed Task #
    path('v2/closed_count_details_per_user/',views.ClosedCountDetailsPerUserV2View.as_view()),
    path('v2/closed_task_details_per_user/',views.ClosedTaskDetailsPerUserV2View.as_view()),
    path('v2/closed_appointment_details_per_user/',views.ClosedAppointmenDetailsPerUserV2View.as_view()),

    # ::::: Closed Task DOWNLOAD ::::: #
    path('v2/closed_task_details_per_user_download/',views.ClosedTaskDetailsPerUserDownloadV2View.as_view()),
    path('v2/closed_appointment_details_per_user_download/',views.ClosedAppointmenDetailsPerUserDownloadV2View.as_view()),

    # teams planner #
    path('v2/ongoing_team_task_details_per_user/',views.TeamTaskDetailsPerUserViewV2.as_view()),
    path('v2/ongoing_team_priority_task_details_per_user/',views.TeamPriorityTaskDetailsPerUserViewV2.as_view()),
    path('v2/upcoming_team_task_details_per_user/',views.TeamUpcomingTaskDetailsPerUserViewV2.as_view()),
    path('v2/upcoming_team_task_reporting_list/',views.TeamsUpcomingReportingDetailsPerUserViewV2.as_view()),
    path('v2/today_team_task_reporting_details_per_user/',views.TeamsTodaysReportingDetailsPerUserViewV2.as_view()),
    path('v2/overdue_team_task_details_per_user/',views.TeamsOverdueTaskDetailsPerUserViewV2.as_view()),

    # ::::: Team Planner DOWNLOAD ::::: #
    path('v2/ongoing_team_task_details_per_user_download/', views.TeamTaskDetailsPerUserDownloadViewV2.as_view()),
    path('v2/ongoing_team_priority_task_details_per_user_download/',views.TeamPriorityTaskDetailsPerUserDownloadViewV2.as_view()),
    path('v2/upcoming_team_task_details_per_user_download/', views.TeamUpcomingTaskDetailsPerUserDownloadViewV2.as_view()),
    path('v2/upcoming_team_task_reporting_list_download/', views.TeamsUpcomingReportingDetailsPerUserDownloadViewV2.as_view()),
    path('v2/today_team_task_reporting_details_per_user_download/', views.TeamsTodaysReportingDetailsPerUserDownloadViewV2.as_view()),
    path('v2/overdue_team_task_details_per_user_download/',views.TeamsOverdueTaskDetailsPerUserDownloadViewV2.as_view()),

    # task reports #
    path('v2/teams_e_task_admin_task_report/', views.ETaskAdminTaskReportViewV2.as_view()),

    # task extenssion list #
    path('v2/etask_requested_extensions_list/',views.EtaskExtensionsRequestListView.as_view()),
    path('v2/team_etask_request_for_extensions_list/',views.TeamEtaskExtensionsRequestListViewV2.as_view()),

    # ::::: etask extenssion list download ::::: #
    path('v2/etask_requested_extensions_list_download/',views.EtaskExtensionsRequestLisDownloadtViewV2.as_view()),
    path('v2/team_etask_request_for_extensions_list_download/',views.TeamEtaskExtensionsRequestListDownloadViewV2.as_view()),

    # ::::: Misc Download ::::: #
    path('v2/etask_task_cc_list_download/',views.EtaskTaskCCListDownloadview.as_view()),
    path('v2/e_task_team_tasks_transferred_list_download/',views.ETaskTeamTasksTransferredListDownloadView.as_view()),
    path('v2/e_task_ownership_tasks_transferred_list_download/',views.ETaskOwnershipTasksTransferredListDownloadView.as_view()),
    path('v2/e_task_default_reporting_dates_add_download/',views.ETaskDefaultReportingDatesDownloadViewV2.as_view()),
    path('v2/teams_e_task_admin_task_report_download/', views.ETaskAdminTaskReportDownloadViewV2.as_view()),
    path('v2/dailysheet_list_download/', views.DailysheetTaskListDownloadView.as_view()),

    # Time Sheet #
    path('v2/dailysheet_task_add/', views.DailysheetTaskAddViewV2.as_view()),
    path('v2/dailysheet_list/', views.DailysheetTaskListViewV2.as_view()),
    path('v2/dailysheet_edit/<pk>/', views.DailySheetEditViewV2.as_view()),
    
    # Time Sheet DropDown #
    path('v2/dailysheel_task_list/',views.DailySheetUserTaskListView.as_view()),
    path('v2/dailysheel_appointment_list/',views.DailySheetAppointmentListView.as_view()),
]
