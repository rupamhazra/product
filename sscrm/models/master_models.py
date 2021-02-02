from django.db import models
from sscrm.models import SSCrmBaseAbstractStructure


class SSCrmCustomer(SSCrmBaseAbstractStructure):
    customer_code = models.CharField(max_length=50, blank=True, null=True)
    customer_name = models.CharField(max_length=250, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    gst = models.CharField(max_length=50, blank=True, null=True)
    pan = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'sscrm_customer'


class SSCrmCustomerCodeType(SSCrmBaseAbstractStructure):
    CODE_TYPE = (
        (1, 'Payer'),
        (2, 'Sold to Party'),
        (3, 'Ship to Party'),
    )
    customer = models.ForeignKey(SSCrmCustomer, on_delete=models.CASCADE, related_name='sscrm_cct_customer')
    code_type = models.IntegerField(choices=CODE_TYPE, blank=True, null=True)
    code = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'sscrm_customer_code_type'


class SSCrmContractType(SSCrmBaseAbstractStructure):
    name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'sscrm_contract_type'
