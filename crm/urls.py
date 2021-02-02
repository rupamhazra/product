from django.urls import path
from crm import views

"""
To execute celery task: $ celery -A SSIL_SSO_MS worker -l info
"""
urlpatterns = [
    # :::::::::::::::::::::::: Database Query ::::::::::::::::::::::::::: #
    path('database_query/', views.CrmDatabaseQueryView.as_view()),

    # :::::::::::::::::::::::: Document ::::::::::::::::::::::::::: #
    path('document_add_or_list/', views.CrmDocumentAddView.as_view()),
    path('document_multi_upload/', views.CrmDocumentMultiUploadView.as_view()),

    # :::::::::::::::::::::::: Department ::::::::::::::::::::::::::: #
    path('department_add_or_list/', views.CrmDepartmentAddView.as_view()),
    path('department_edit/<pk>/', views.CrmDepartmentEditView.as_view()),
    path('department_delete/<pk>/', views.CrmDepartmentDeleteView.as_view()),

    # :::::::::::::::::::::::: Resource ::::::::::::::::::::::::::: #
    path('resource_add_or_list/', views.CrmResourceAddView.as_view()),
    path('resource_edit/<pk>/', views.CrmResourceEditView.as_view()),
    path('resource_delete/<pk>/', views.CrmResourceDeleteView.as_view()),

    # :::::::::::::::::::::::: DocumentTag ::::::::::::::::::::::::::: #
    path('document_tag_add_or_list/', views.CrmDocumentTagAddView.as_view()),
    path('document_tag_edit/<pk>/', views.CrmDocumentTagEditView.as_view()),
    path('document_tag_delete/<pk>/', views.CrmDocumentTagDeleteView.as_view()),

    # :::::::::::::::::::::::: Technology ::::::::::::::::::::::::::: #
    path('technology_add_or_list/', views.CrmTechnologyAddView.as_view()),
    path('technology_edit/<pk>/', views.CrmTechnologyEditView.as_view()),
    path('technology_delete/<pk>/', views.CrmTechnologyDeleteView.as_view()),

    # :::::::::::::::::::::::: Source ::::::::::::::::::::::::::: #
    path('source_add_or_list/', views.CrmSourceAddView.as_view()),
    path('source_edit/<pk>/', views.CrmSourceEditView.as_view()),
    path('source_delete/<pk>/', views.CrmSourceDeleteView.as_view()),

    # :::::::::::::::::::::::: PaymentMode ::::::::::::::::::::::::::: #
    path('payment_mode_add_or_list/', views.CrmPaymentModeAddView.as_view()),
    path('payment_mode_edit/<pk>/', views.CrmPaymentModeEditView.as_view()),
    path('payment_mode_delete/<pk>/', views.CrmPaymentModeDeleteView.as_view()),

    # :::::::::::::::::::::::: ColorStatus ::::::::::::::::::::::::::: #
    path('color_status_add_or_list/', views.CrmColorStatusAddView.as_view()),
    path('color_status_edit/<pk>/', views.CrmColorStatusEditView.as_view()),
    path('color_status_delete/<pk>/', views.CrmColorStatusDeleteView.as_view()),

    # :::::::::::::::::::::::: Task ::::::::::::::::::::::::::: #
    path('task_update/<pk>/', views.CrmTaskUpdateView.as_view()),

    # :::::::::::::::::::::::: Poc ::::::::::::::::::::::::::: #
    path('poc_update/<pk>/', views.CrmPocUpdateView.as_view()),

    # :::::::::::::::::::::::: User ::::::::::::::::::::::::::: #
    path('user_type_list/', views.CrmUserListByTypeView.as_view()),
    path('user_list_by_role_module/', views.CrmUserListByRoleModuleView.as_view()),
    path('users_under_reporting_head/', views.CrmUsersUnderReportingHeadView.as_view()),

    # :::::::::::::::::::::::: Lead ::::::::::::::::::::::::::: #
    path('lead_list/', views.CrmLeadListView.as_view()),
    path('lead_create/', views.CrmLeadCreateView.as_view()),
    path('lead_update/<pk>/', views.CrmLeadUpdateView.as_view()),
    path('lead_bulk_upload/', views.CrmLeadBulkUploadView.as_view()),
    # path('lead_status_update/<pk>/', views.CrmLeadStatusUpdateView.as_view()), # TODO: Use 'status_update_multi_lead/'
    path('lead_assign/', views.CrmLeadAssignView.as_view()),
    path('lead_details/<pk>/', views.CrmLeadDetailsView.as_view()),
    path('status_update_multi_lead/', views.CrmStatusUpdateMultiLeadView.as_view()),
    path('add_task_to_lead/<pk>/', views.CrmAddTaskToLeadView.as_view()),
    path('lead_request_reassign/<pk>/', views.CrmLeadRequestReassignView.as_view()),

    path('opportunity_create/', views.CrmOpportunityCreateView.as_view()),
    path('opportunity_file_upload/<pk>/', views.CrmOpportunityFileUploadView.as_view()),

    # :::::::::::::::::::::::: Pipeline :::::::::::::::::::::::: #
    path('opportunity_snapshot_list/', views.CrmOpportunitySnapshotListView.as_view()),
    path('opportunity_list_group_by_stage/', views.CrmOpportunityListGroupByStageView.as_view()),

    path('opportunity_presale_update/<pk>/', views.CrmOpportunityPresaleUpdateView.as_view()),
    path('opportunity_proposal_update/<pk>/', views.CrmOpportunityProposalUpdateView.as_view()),
    path('opportunity_agreement_upload/<pk>/', views.CrmOpportunityAgreementUploadView.as_view()),

    path('opportunity_update/<pk>/', views.CrmOpportunityUpdateView.as_view()),
    path('opportunity_ba_update/<pk>/', views.CrmOpportunityBAUpdateView.as_view()),
    path('opportunity_hour_consume_update/<pk>/', views.CrmOpportunityHourConsumeUpdateView.as_view()),
    path('opportunity_document_delete_retrieve/<pk>/', views.CrmOpportunityDocumentDeleteRetrieveView.as_view()),

    path('request_create/', views.CrmRequestCreateView.as_view()),
    path('request_accept/<pk>/', views.CrmRequestAcceptView.as_view()),
    path('request_complete/<pk>/', views.CrmRequestCompleteView.as_view()),

    path('opportunity_color_status_update/<pk>/', views.CrmOpportunityColorStatusUpdateView.as_view()),
    path('opportunity_tag_update/<pk>/', views.CrmOpportunityTagUpdateView.as_view()),
    path('opportunity_stage_or_status_update/<pk>/', views.CrmOpportunityStageStatusUpdateView.as_view()),
    path('add_task_to_opportunity/<pk>/', views.CrmAddTaskToOpportunityView.as_view()),

    path('check_if_project_from_open/', views.CrmCheckIfProjectFormOpenView.as_view()),
    path('project_form_open_or_cancel/<pk>/', views.CrmProjectFormOpenOrCancelView.as_view()),
    path('project_create/', views.CrmProjectCreateView.as_view()),

    # :::::::::::::::::::::::: Account :::::::::::::::::::::::: #
    path('account_list/', views.CrmAccountListView.as_view()),
    path('add_poc_to_opportunity/<pk>/', views.CrmAddPocToOpportunityView.as_view()),
    path('add_milestone_to_opportunity/<pk>/', views.CrmAddMilestoneToOpportunityView.as_view()),
    path('update_milestone_in_opportunity/<pk>/', views.CrmUpdateMilestoneInOpportunityView.as_view()),
    path('delete_milestone_from_opportunity/<pk>/', views.CrmDeleteMilestoneFromOpportunityView.as_view()),
    path('add_change_request_to_opportunity/<pk>/', views.CrmAddChangeRequestToOpportunityView.as_view()),
    path('update_change_request_in_opportunity/<pk>/', views.CrmUpdateChangeRequestInOpportunityView.as_view()),
    path('change_request_details_opportunity_wise/<pk>/', views.CrmChangeRequestDetailsOpportunityWiseView.as_view()),
    path('opportunity_details/<pk>/', views.CrmOpportunityDetailsView.as_view()),
    path('opportunity_poc_update_primary/<pk>/', views.CrmOpportunityPocUpdatePrimaryView.as_view()),

    # :::::::::::::::::::::::: Lost Won :::::::::::::::::::::::: #
    path('close_won_list/', views.CrmCloseWonListView.as_view()),

    # :::::::::::::::::::::::: Loss Analysis :::::::::::::::::::::::: #
    path('loss_analysis_list/', views.CrmLossAnalysisListView.as_view()),

    # :::::::::::::::::::::::::::: Filter :::::::::::::::::::::::::::: #
    path('account_lead_filter_list/', views.CrmAccountLeadFilterListView.as_view()),
    path('user_filter_list/', views.CrmUserFilterListView.as_view()),

    # :::::::::::::::::::::::: Report :::::::::::::::::::::::: #
    path('lead_report/', views.CrmLeadReportListView.as_view()),
    path('customer_report/', views.CrmCustomerReportListView.as_view()),
    path('invoice_report/', views.CrmInvoiceReportListView.as_view()),
    path('project_report/', views.CrmProjectReportListView.as_view()),

]
