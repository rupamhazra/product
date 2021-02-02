from django.urls import path
from sscrm import views

urlpatterns = [

    # :::::::::::::::::::::::: Customer ::::::::::::::::::::::::::: #
    path('customer_add_or_list/', views.SSCrmCustomerAddView.as_view()),
    path('customer_edit/<pk>/', views.SSCrmCustomerEditView.as_view()),
    path('customer_delete/<pk>/', views.SSCrmCustomerDeleteView.as_view()),

    #:::::::::::::::::::::::: CustomerCodeType ::::::::::::::::::::::::::: #
    path('customer_code_type_type_add_or_list/', views.SSCrmCustomerCodeTypeAddView.as_view()),
    path('customer_code_type_type_edit/<pk>/', views.SSCrmCustomerCodeTypeEditView.as_view()),
    path('customer_code_type_type_delete/<pk>/', views.SSCrmCustomerCodeTypeDeleteView.as_view()),

    #:::::::::::::::::::::::: ContractType ::::::::::::::::::::::::::: #
    path('contract_type_add_or_list/', views.SSCrmContractTypeAddView.as_view()),
    path('contract_type_edit/<pk>/', views.SSCrmContractTypeEditView.as_view()),
    path('contract_type_delete/<pk>/', views.SSCrmContractTypeDeleteView.as_view()),


]
