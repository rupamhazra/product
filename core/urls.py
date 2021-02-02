from core import views
from django.conf.urls import url, include
from rest_framework import routers
from django.urls import path
from rest_framework.authtoken import views as rest_framework_views

'''
    This module prepared by @@ Rupam Hazra. Any kind of issues occurred, ask me first !!!
    Version - 1.0
'''

urlpatterns = [
    path('permissions_list/', views.PermissionsListCreate.as_view()),
    path('add_application/', views.ModuleListCreate.as_view()),
    path('applications_list/', views.ModuleList.as_view()),
    path('edit_application/<pk>/', views.EditModuleById.as_view()),
    path('add_role/', views.RoleListCreate.as_view()), #add role and list of role
    path('edit_role/<pk>/', views.RoleRetrieveUpdateAPIView.as_view()), #add role and list of role
    path('unit_add/', views.UnitAddView.as_view()),
    
    #:::::::::::::::: OBJECTS :::::::::::::#
    path('other_add/', views.OtherAddView.as_view()),
    path('other_list/<module_id>/', views.OtherListView.as_view()),
    path('other_list_by_parent/<module_id>/<parent_id>/', views.OtherListByParentView.as_view()),
    path('other_edit/<pk>/', views.OtherEditView.as_view()),
    path('other_delete/<pk>/', views.OtherDeleteView.as_view()),

    # Objects List For Role
    path('other_list_for_role/<module_id>/', views.OtherListForRoleView.as_view()),
    
    #:::::::::::::::::::::: T CORE DEPARTMENT:::::::::::::::::::::::::::#
    path('t_core_department_add/', views.CoreDepartmentAddView.as_view()),
    path('t_core_department_add_with_child_dep/<parent_id>/', views.CoreDepartmentWithChildView.as_view()),
    path('t_core_department_edit/<pk>/', views.CoreDepartmentEditView.as_view()),
    path('t_core_department_delete/<pk>/', views.CoreDepartmentDeleteView.as_view()),
    path('t_core_department_list/', views.CoreDepartmentListView.as_view()),
    #:::::::::::::::::::::: T CORE DESIGNATION:::::::::::::::::::::::::::#
    path('t_core_designation_add/', views.CoreDesignationAddView.as_view()),
    path('t_core_designation_edit/<pk>/', views.CoreDesignationEditView.as_view()),
    path('t_core_designation_delete/<pk>/', views.CoreDesignationDeleteView.as_view()),
    path('t_core_designation_list/',views.CoreDesignationListView.as_view()),

    #:::::::::::::::::::::: T CORE COMPANY :::::::::::::::::::::::::::::#
    path('t_core_company_add/',views.CoreCompanyAddView.as_view()),
    path('t_core_company_edit/<pk>/',views.CoreCompanyEditView.as_view()),
    path('t_core_comapny_delete/<pk>/',views.CoreCompanyDeleteView.as_view()),
    path('t_core_comapny_list/',views.CoreCompanyListView.as_view()),

    #::::::::::::::::::::::::::::COMPANY COST CENTRE ::::::::::::::::::::::#
    path('core/company_cost_centre_add/',views.CompanyCostCentreAddView.as_view()),
    path('core/company_cost_centre_edit/<pk>/',views.CompanyCostCentreEditView.as_view()),
    path('core/company_cost_centre_list/',views.CompanyCostCentreListView.as_view()),
    path('core/company_cost_centre_list_without_pagination/',views.CompanyCostCentreWithOutPaginationListView.as_view()),
    path('core/company_cost_centre_delete/<pk>/',views.CompanyCostCentreDeleteView.as_view()),
    # ::::::::::::::::::::::::::: T CORE GRADE ADD ::::::::::::::::::::::::::
    path('t_core_grade_add/',views.CoreGradeAddView.as_view()),
    path('t_core_grade_list/',views.CoreGradeListView.as_view()),
    path('t_core_grade_edit/<pk>/',views.CoreGradeEditView.as_view()),
    path('t_core_grade_delete/<pk>/',views.CoreGradeDeleteView.as_view()),

    # ::::::::::::::::::::::::::: T CORE SUB GRADE ADD ::::::::::::::::::::::::::
    path('t_core_sub_grade_add/',views.CoreSubGradeAddView.as_view()),
    path('t_core_sub_grade_list/',views.CoreSubGradeListView.as_view()),
    path('t_core_sub_grade_list_wp/',views.CoreSubGradeListWithOutPaginationView.as_view()),
    path('t_core_sub_grade_edit/<pk>/',views.CoreSubGradeEditView.as_view()),
    path('t_core_sub_grade_delete/<pk>/',views.CoreSubGradeDeleteView.as_view()),


    ###################################################################
    ########################### new permission level API ##############
    ###################################################################

    #:::::::::::::::: OBJECTS :::::::::::::#

    path('other_add_new/', views.OtherAddNewView.as_view()),
    path('other_list_new_by_module_name/<module_name>/', views.OtherListNewView.as_view()),
    path('other_list_with_permission_by_role_module_name/<module_name>/<role_name>/',views.OtherListWithPermissionByRoleModuleNameView.as_view()),
    path('other_list_with_permission_by_user_module_name/<module_name>/<user_id>/',views.OtherListWithPermissionByUserModuleNameView.as_view()),
    path('other_edit_new/<pk>/', views.OtherEditNewView.as_view()),

    #::::::::::::::: T Core State ::::::::::::::::#
    path('states_list_add/',views.StatesListAddView.as_view()),
    path('all_states_list_add/',views.AllStatesListAddView.as_view()), # including deleted
    path('states_list_edit/<pk>/',views.StatesListEditView.as_view()),
    path('states_list_delete/<pk>/',views.StatesListDeleteView.as_view()),
    #:::::::::::::::::::::: T CORE SALARY TYPE:::::::::::::::::::::::::::#
    path('t_core_salary_type_add/', views.CoreSalaryTypeAddView.as_view()),
    path('t_core_salary_type_edit/<pk>/', views.CoreSalaryTypeEditView.as_view()),
    path('t_core_salary_type_delete/<pk>/', views.CoreSalaryTypeDeleteView.as_view()),

    #::: Sub Department :::#
    path('t_core_sub_department/<dept_id>/', views.CoreSubDepartmentView.as_view()),

    #::::::::: T CORE BANK :::::::::#
    path('t_core_bank_add/', views.CoreBankAddView.as_view()),
    path('t_core_bank_edit/<pk>/', views.CoreBankEditView.as_view()),
    path('t_core_bank_delete/<pk>/', views.CoreBankDeleteView.as_view()),
    path('t_core_bank_list/',views.CoreBankListView.as_view()),

    #::::::::: T CORE Country :::::::::#
    path('t_core_country_add_or_list/', views.CoreCountryAddView.as_view()),
    path('t_core_country_edit/<pk>/', views.CoreCountryEditView.as_view()),
    path('t_core_country_delete/<pk>/', views.CoreCountryDeleteView.as_view()),

    #::::::::: T CORE Currency :::::::::#
    path('t_core_currency_add_or_list/', views.CoreCurrencyAddView.as_view()),
    path('t_core_currency_create/', views.CoreCurrencyCreateView.as_view()),
    path('t_core_currency_edit/<pk>/', views.CoreCurrencyEditView.as_view()),
    path('t_core_currency_delete/<pk>/', views.CoreCurrencyDeleteView.as_view()),

    #::::::::: T CORE Domain :::::::::#
    path('t_core_domain_add_or_list/', views.CoreDomainAddView.as_view()),
    path('t_core_domain_edit/<pk>/', views.CoreDomainEditView.as_view()),
    path('t_core_domain_delete/<pk>/', views.CoreDomainDeleteView.as_view()),

    #:::::::::::::::::::::: T CORE CITY :::::::::::::::::::::::::::::#
    path('t_core_city_add/',views.CoreCityAddView.as_view()),
    path('t_core_city_edit/<pk>/',views.CoreCityEditView.as_view()),
    path('t_core_city_delete/<pk>/',views.CoreCityDeleteView.as_view()),
    path('t_core_city_list/',views.CoreCityListView.as_view()),

    # Floor List
    path('core/floor/list/',views.FloorListView.as_view()),
]