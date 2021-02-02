from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from core.models import *
from django.contrib.auth.models import *
from rest_framework.exceptions import APIException
from django.conf import settings
# from rest_framework.validators import *
from drf_extra_fields.fields import Base64ImageField # for image base 64
from django.db import transaction, IntegrityError
from master.models import TMasterModuleOther,TMasterOtherRole,TMasterOtherUser,TMasterModuleRoleUser
from users.models import *

class TCorePermissionsSerializer(serializers.ModelSerializer):
    cp_created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TCorePermissions
        fields = ('id','name','cp_created_by')


class TCoreModuleSerializer(serializers.ModelSerializer):
    cm_created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TCoreModule
        fields = ('id','cm_name','cm_icon','cm_desc','cm_url',
                   'cm_created_by', 'cm_is_editable')

class TCoreModuleListSerializer(serializers.ModelSerializer):
    """docstring for ClassName"""
    # cm_icon = Base64ImageField()    
    
    class Meta:
        model = TCoreModule
        fields = ('id','cm_name', 'cm_icon','cm_desc','cm_url')

class TCoreRoleSerializer(serializers.ModelSerializer):
    """docstring for ClassName"""
    cr_created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TCoreRole
        fields = ('id','cr_name', 'cr_parent_id', 'cr_created_by','cr_is_deleted')

class UnitAddSerializer(serializers.ModelSerializer):
    c_created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    c_owned_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreUnit
        fields = ('id', 'c_name', 'c_created_by', 'c_owned_by')

#:::::::::::::::: OBJECTS :::::::::::::#

class OtherAddSerializer(serializers.ModelSerializer):
    cot_created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    cot_parent_id = serializers.IntegerField(required=False)
    mmo_module = serializers.CharField(required=False)
    class Meta:
        model = TCoreOther
        fields = ('id','cot_name','description','cot_parent_id','cot_created_by','mmo_module')
    def create(self, validated_data):
        try:
            cot_created_by = validated_data.get('cot_created_by')
            cot_parent_id = validated_data.pop('cot_parent_id') if 'cot_parent_id' in validated_data else 0
            with transaction.atomic():
                cot_save_id = TCoreOther.objects.create(
                    cot_name=validated_data.get('cot_name'),
                    description=validated_data.get('description'),
                    cot_parent_id = cot_parent_id,
                    cot_created_by=cot_created_by,
                )
                master_module = TMasterModuleOther.objects.create(
                    mmo_other = cot_save_id,
                    mmo_module_id = validated_data.get('mmo_module'),

                )
                response = {
                    'id': cot_save_id.id,
                    'cot_name': cot_save_id.cot_name,
                    'description': cot_save_id.description,
                    'mmo_module':master_module.mmo_module,
                    'cot_parent_id':cot_save_id.cot_parent_id
                }
                return response
        except Exception as e:
            raise e

class OtherListSerializer(serializers.ModelSerializer):
    #parent_name = serializers.CharField(required=False)
    class Meta:
        model = TMasterModuleOther
        fields = ('id','mmo_other','mmo_module','is_deleted')

class OtherListForRoleSerializer(serializers.ModelSerializer):
    permission = serializers.CharField(required=False)
    class Meta:
        model = TMasterModuleOther
        fields = ('id','mmo_other','mmo_module','is_deleted','permission')

class OtherEditSerializer(serializers.ModelSerializer):
    cot_updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    cot_parent_id = serializers.IntegerField(required=False)
    mmo_module = serializers.CharField(required=False)
    class Meta:
        model = TCoreOther
        fields = ('id', 'cot_name', 'description', 'cot_parent_id', 'cot_updated_by', 'mmo_module')

    def update(self, instance, validated_data):
        try:
            print('validated_data',validated_data)
            cot_updated_by = validated_data.get('cot_updated_by')
            cot_parent_id = validated_data.pop('cot_parent_id') if 'cot_parent_id' in validated_data else 0
            with transaction.atomic():
                instance.cot_name = validated_data.get('cot_name')
                instance.description = validated_data.get('description')
                instance.cot_parent_id = cot_parent_id
                instance.cot_updated_by = cot_updated_by
                instance.save()

                tMasterModuleOther = TMasterModuleOther.objects.filter(
                    mmo_other=instance.id)
                print('tMasterModuleOther',tMasterModuleOther)
                if tMasterModuleOther:
                    tMasterModuleOther.delete()

                master_module = TMasterModuleOther.objects.create(
                    mmo_other = instance,
                    mmo_module_id = validated_data.get('mmo_module'),
                )
                #print('master_module', master_module)
                response = {
                    'id': instance.id,
                    'cot_name': instance.cot_name,
                    'description': instance.description,
                    'mmo_module':master_module.mmo_module,
                    'cot_parent_id':instance.cot_parent_id
                }
                return response
        except Exception as e:
            raise e

class OtherDeleteSerializer(serializers.ModelSerializer):
    cot_updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault(),required=False)
    parent_id = serializers.IntegerField(required=False)
    mmo_module = serializers.CharField(required=False)
    is_deleted = serializers.CharField(required=False)
    class Meta:
        model = TCoreOther
        fields = ('id', 'cot_name', 'description', 'parent_id', 'cot_updated_by',
                  'mmo_module','updated_by','is_deleted')

    def update(self, instance, validated_data):
        try:
            cot_updated_by = validated_data.get('cot_updated_by')
            updated_by = validated_data.get('updated_by')
            instance.cot_is_deleted = True
            instance.cot_updated_by = cot_updated_by
            instance.save()
            #print('instance',instance)
            module_other = TMasterModuleOther.objects.filter(mmo_other=instance)
            #print('ModuleOther',module_other.query)
            for e_module_other in module_other:
                e_module_other.is_deleted = True
                e_module_other.updated_by = updated_by
                e_module_other.save()
            return instance
        except Exception as e:
            raise e

#:::::::::::::::::::::: T CORE DEPARTMENT:::::::::::::::::::::::::::#
class CoreDepartmentAddSerializer(serializers.ModelSerializer):
    cd_created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TCoreDepartment
        fields = ('id', 'cd_name', 'cd_parent_id','cd_is_deleted', 'cd_created_by', 'cd_created_at', 'cd_updated_at', 'cd_updated_by', 'cd_deleted_at', 'cd_deleted_by')


class CoreDepartmentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TCoreDepartment
        fields = "__all__"

class CoreDepartmentEditSerializer(serializers.ModelSerializer):
    cd_updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreDepartment
        fields = ('id', 'cd_name','cd_parent_id','cd_is_deleted', 'cd_created_by', 'cd_created_at', 'cd_updated_at', 'cd_updated_by', 'cd_deleted_at', 'cd_deleted_by')

class CoreDepartmentDeleteSerializer(serializers.ModelSerializer):
    cd_deleted_by = serializers.CharField(default=serializers.CurrentUserDefault())
    is_confirm = serializers.BooleanField(required=False, default=False)
    warning = serializers.BooleanField(required=False, default=False)
    class Meta:
        model = TCoreDepartment
        fields = '__all__'
    def update(self, instance, validated_data):
        is_confirm = validated_data.get('is_confirm')
        if not is_confirm:
            pk = instance.id
            # print(pk)
            usr_obj = TCoreUserDetail.objects.filter(department__id=instance.id).count()
            # print(usr_obj)
            if usr_obj:
                # print("mot deleted")
                instance.warning = True
                return instance
            else:
                instance.cd_is_deleted = True
                instance.cd_deleted_by = validated_data.get('cd_deleted_by')
                instance.save()
                return instance
        else:
            instance.cd_is_deleted = True
            instance.cd_deleted_by = validated_data.get('cd_deleted_by')
            instance.save()
            return instance


#:::::::::::::::::::::: T CORE DESIGNATION:::::::::::::::::::::::::::#
class CoreDesignationAddSerializer(serializers.ModelSerializer):
    cod_created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    mmr_module = serializers.SerializerMethodField()
    def get_mmr_module(self,TCoreDesignation):
        module_details = TMasterModuleRoleUser.objects.filter(mmr_designation_id=TCoreDesignation.id)[:0]  
        if module_details:
            return str(TMasterModuleRoleUser.objects.only('mmr_module').get(mmr_designation_id=TCoreDesignation.id).mmr_module)    
        else:
            return None

    class Meta:
        model = TCoreDesignation
        fields = ('id', 'cod_name', 'cod_is_deleted', 'cod_created_by', 'cod_created_at', 
        'cod_updated_at', 'cod_updated_by', 'cod_deleted_at', 'cod_deleted_by','mmr_module')

class CoreDesignationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TCoreDesignation
        fields = '__all__'

class CoreDesignationEditSerializer(serializers.ModelSerializer):
    cod_updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreDesignation
        fields = ('id', 'cod_name', 'cod_is_deleted', 'cod_created_by', 'cod_created_at', 'cod_updated_at', 'cod_updated_by', 'cod_deleted_at', 'cod_deleted_by')

class CoreDesignationDeleteSerializer(serializers.ModelSerializer):
    cod_deleted_by = serializers.CharField(default=serializers.CurrentUserDefault())
    is_confirm = serializers.BooleanField(required=False,default=False)
    warning = serializers.BooleanField(required=False,default=False)
    class Meta:
        model = TCoreDesignation
        fields = '__all__'
    def update(self, instance, validated_data):
        is_confirm = validated_data.get('is_confirm')
        if not is_confirm:
            pk = instance.id
            # print(pk)
            usr_obj = TCoreUserDetail.objects.filter(designation__id=instance.id).count()
            # print(usr_obj)
            if usr_obj:
                # print("mot deleted")
                instance.warning = True
                return instance
            else:
                instance.cod_is_deleted = True
                instance.cod_deleted_by = validated_data.get('cod_deleted_by')
                instance.save()
                return instance
        else:
            instance.cod_is_deleted = True
            instance.cod_deleted_by = validated_data.get('cod_deleted_by')
            instance.save()
            return instance

# :::::::::::::::::::::::::::::::::: T CORE SUB GRADE ::::::::::::::::::::::::::::::::::::::::::::::::::
class CoreSubGradeAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TCoreSubGrade
        fields = ('__all__')

class CoreSubGradeEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreSubGrade
        fields = ('__all__')

class CoreSubGradeDeleteSerializer(serializers.ModelSerializer):
    deleted_by = serializers.CharField(default=serializers.CurrentUserDefault())
    is_confirm = serializers.BooleanField(required=False, default=False)
    warning = serializers.BooleanField(required=False, default=False)
    class Meta:
        model = TCoreSubGrade
        fields = '__all__'
    def update(self, instance, validated_data):
        is_confirm = validated_data.get('is_confirm')
        if not is_confirm:
            usr_obj = TCoreUserDetail.objects.filter(employee_sub_grade__id=instance.id).count()
            # print(usr_obj)
            if usr_obj:
                # print("mot deleted")
                instance.warning = True
                return instance
            else:
                instance.is_deleted = True
                instance.deleted_by = validated_data.get('deleted_by')
                instance.save()
                return instance
        else:
            print("in else")
            instance.is_deleted = True
            instance.deleted_by = validated_data.get('deleted_by')
            instance.save()
            return instance

class CoreSubGradeListSerializer(serializers.ModelSerializer):
    parent_sub_grade_name = serializers.SerializerMethodField()

    def get_parent_sub_grade_name(self,obj):
        if obj.parent_id:
            return TCoreSubGrade.objects.get(id=obj.parent_id).name
        else:
            return None

    class Meta:
        model = TCoreSubGrade
        fields = ('__all__')
        extra_fields = ("parent_sub_grade_name")
# :::::::::::::::::::::::::::::::T CORE GRADE :::::::::::::::::::::::::::::::::::::::::

class CoreGradeAddSerializer(serializers.ModelSerializer):
    cg_created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TCoreGrade
        fields = ('__all__')

class CoreGradeEditSerializer(serializers.ModelSerializer):
    cg_updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreGrade
        fields = ('__all__')

class CoreGradeDeleteSerializer(serializers.ModelSerializer):
    cg_deleted_by = serializers.CharField(default=serializers.CurrentUserDefault())
    is_confirm = serializers.BooleanField(required=False, default=False)
    warning = serializers.BooleanField(required=False, default=False)
    class Meta:
        model = TCoreGrade
        fields = '__all__'
    def update(self, instance, validated_data):
        is_confirm = validated_data.get('is_confirm')
        if not is_confirm:
            usr_obj = TCoreUserDetail.objects.filter(employee_grade=instance)
            print('usr_obj',usr_obj.query)
            if usr_obj:
                # print("mot deleted")
                instance.warning = True
                return instance
            else:
                instance.cg_is_deleted = True
                instance.cg_deleted_by = validated_data.get('cg_deleted_by')
                instance.save()
                return instance
        else:
            print("in else")
            instance.cg_is_deleted = True
            instance.cg_deleted_by = validated_data.get('cg_deleted_by')
            instance.save()
            return instance

class CoreGradeListSerializer(serializers.ModelSerializer):
    parent_grade_name = serializers.SerializerMethodField()

    def get_parent_grade_name(self,obj):
        if obj.cg_parent_id:
            return TCoreGrade.objects.get(id=obj.cg_parent_id).cg_name
        else:
            return None

    class Meta:
        model = TCoreGrade
        fields = ('__all__')
        extra_fields = ("parent_grade_name")

#:::::::::::::::::::::: T CORE COMPANY :::::::::::::::::::::::::::::#
class CoreCompanyAddSerializer(serializers.ModelSerializer):
    coc_created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TCoreCompany
        fields = ('__all__')

class CoreCompanyListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TCoreCompany
        fields = ('__all__')

class CoreCompanyEditSerializer(serializers.ModelSerializer):
    coc_updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreCompany
        fields = ('__all__')


class CoreCompanyDeleteSerializer(serializers.ModelSerializer):
    coc_deleted_by = serializers.CharField(default=serializers.CurrentUserDefault())
    is_confirm = serializers.BooleanField(required=False, default=False)
    warning = serializers.BooleanField(required=False, default=False)
    class Meta:
        model = TCoreCompany
        fields = '__all__'
    def update(self, instance, validated_data):
        is_confirm = validated_data.get('is_confirm')
        if not is_confirm:
            pk = instance.id
            # print(pk)
            usr_obj = TCoreUserDetail.objects.filter(company__id=instance.id).count()
            # print(usr_obj)
            if usr_obj:
                # print("mot deleted")
                instance.warning = True
                return instance
            else:
                instance.cod_is_deleted = True
                instance.cod_deleted_by = validated_data.get('coc_deleted_by')
                instance.save()
                return instance
        else:
            instance.coc_is_deleted = True
            instance.coc_deleted_by = validated_data.get('coc_deleted_by')
            instance.save()
            return instance

#:::::::::::::::::::::: COMPANY COST CENTRE :::::::::::::::::::::::::::::#
class CompanyCostCentreAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TCoreCompanyCostCentre
        fields = ('__all__')

class CompanyCostCentreEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreCompanyCostCentre
        fields = ('__all__')

class CompanyCostCentreListSerializer(serializers.ModelSerializer):
    company_id = serializers.SerializerMethodField(required=False)
    company_name = serializers.SerializerMethodField(required=False)

    def get_company_id(self, obj):
        if obj.company:
            return obj.company.id
        else:
            return None
    def get_company_name(self,obj):
        if obj.company:
            return obj.company.coc_name
        else:
            return None
    class Meta:
        model = TCoreCompanyCostCentre
        fields = ('id', 'company_id','company_name','cost_centre_name','cost_centre_code','created_at','updated_at')

class CompanyCostCentreDeleteSerializer(serializers.ModelSerializer):
    deleted_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TCoreCompanyCostCentre
        fields = '__all__'
    def update(self, instance, validated_data):
        instance.is_deleted = True
        instance.deleted_by = validated_data.get('deleted_by')
        instance.save()
        return instance


class OtherAddNewSerializer(serializers.ModelSerializer):
    cot_created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    cot_parent_id = serializers.IntegerField(required=False)
    mmo_module = serializers.CharField(required=False)
    class Meta:
        model = TCoreOther
        fields = ('id','cot_name','description','cot_parent_id','cot_created_by','mmo_module')
    def create(self, validated_data):
        try:
            cot_created_by = validated_data.get('cot_created_by')
            cot_parent_id = validated_data.pop('cot_parent_id') if 'cot_parent_id' in validated_data else 0
            with transaction.atomic():
                cot_save_id = TCoreOther.objects.create(
                    cot_name=validated_data.get('cot_name'),
                    description=validated_data.get('description'),
                    cot_parent_id = cot_parent_id,
                    cot_created_by=cot_created_by,
                )
                module_id = TCoreModule.objects.only('id').get(cm_name=validated_data.get('mmo_module')).id
                print('module_id',module_id)
                master_module = TMasterModuleOther.objects.create(
                    mmo_other = cot_save_id,
                    mmo_module_id = module_id,

                )
                response = {
                    'id': cot_save_id.id,
                    'cot_name': cot_save_id.cot_name,
                    'description': cot_save_id.description,
                    'mmo_module':master_module.mmo_module,
                    'cot_parent_id':cot_save_id.cot_parent_id
                }
                return response
        except Exception as e:
            raise e

class OtherListWithPermissionByRoleModuleNameSerializer(serializers.ModelSerializer):
    mor_permissions_n = serializers.IntegerField(required=False)
    class Meta:
        model = TMasterOtherRole
        fields = ('id','mor_other','mor_module','mor_role','mor_permissions','mor_permissions_n')

class OtherEditNewSerializer(serializers.ModelSerializer):
    cot_updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    cot_parent_id = serializers.IntegerField(required=False)
    class Meta:
        model = TCoreOther
        fields = ('id', 'cot_name', 'description', 'cot_parent_id', 'cot_updated_by')

    def update(self, instance, validated_data):
        try:
            cot_updated_by = validated_data.get('cot_updated_by')
            with transaction.atomic():
                instance.cot_name = validated_data.get('cot_name')
                instance.description = validated_data.get('description')
                instance.cot_updated_by = cot_updated_by
                instance.save()
                response = {
                    'id': instance.id,
                    'cot_name': instance.cot_name,
                    'description': instance.description,
                    'cot_parent_id':instance.cot_parent_id
                }
                return response
        except Exception as e:
            raise e

class OtherListWithPermissionByUserModuleNameSerializer(serializers.ModelSerializer):
    mou_permissions_n = serializers.IntegerField(required=False)
    mor_other = serializers.IntegerField(required=False)
    mor_module = serializers.IntegerField(required=False)
    mor_permissions = serializers.IntegerField(required=False)
    mor_permissions_n = serializers.IntegerField(required=False)

    class Meta:
        model = TMasterOtherUser
        fields = ('id','mou_other','mou_module','mou_permissions',
        'mou_permissions_n','mor_other','mor_module','mor_permissions','mor_permissions_n')

class StatesListAddSerializer(serializers.ModelSerializer):
    cs_created_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreState
        fields = ('id','cs_state_name','cs_tin_number','cs_state_code','cs_status','cs_created_by')


class AllStatesListAddSerializer(serializers.ModelSerializer):
    cs_created_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreState
        fields = ('id','cs_state_name','cs_tin_number','cs_state_code','cs_status','cs_is_deleted','cs_created_by')


class StatesListEditSerializer(serializers.ModelSerializer):
    cs_updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreState
        fields = ('id','cs_state_name','cs_tin_number','cs_state_code','cs_status','cs_updated_by')

class StatesListDeleteSerializer(serializers.ModelSerializer):
    cs_updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TCoreState
        fields = '__all__'
    def update(self, instance, validated_data):
        instance.cs_is_deleted=True
        instance.cs_status=False
        instance.cs_updated_by = validated_data.get('cs_updated_by')
        instance.save()
        return instance

#:::::::::::::::::::::: T CORE SALARY TYPE:::::::::::::::::::::::::::#
class CoreSalaryTypeAddSerializer(serializers.ModelSerializer):
    st_created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TCoreSalaryType
        fields = '__all__'


class CoreSalaryTypeEditSerializer(serializers.ModelSerializer):
    st_updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreSalaryType
        fields = '__all__'

class CoreSalaryTypeDeleteSerializer(serializers.ModelSerializer):
    st_updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    st_deleted_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TCoreSalaryType
        fields = '__all__'
    def update(self, instance, validated_data):
        instance.is_deleted=True
        instance.st_updated_by = validated_data.get('st_updated_by')
        instance.st_deleted_by = validated_data.get('st_deleted_by')
        instance.save()
        return instance


#:::::::::::::::::::::: T CORE BANK :::::::::::::::::::::::::::#
class CoreBankAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TCoreBank
        fields = '__all__'


class CoreBankEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreBank
        fields = '__all__'

class CoreBankDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    deleted_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TCoreBank
        fields = '__all__'
    def update(self, instance, validated_data):
        instance.is_deleted=True
        instance.updated_by = validated_data.get('updated_by')
        instance.deleted_by = validated_data.get('deleted_by')
        instance.save()
        return instance

class CoreBankListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TCoreBank
        fields = ('__all__')


#:::::::::::::::::::::: T CORE Country :::::::::::::::::::::::::::#
class CoreCountryAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreCountry
        fields = '__all__'


class CoreCountryEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreCountry
        fields = '__all__'


class CoreCountryDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    deleted_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreCountry
        fields = '__all__'

    def update(self, instance, validated_data):
        instance.is_deleted=True
        instance.updated_by = validated_data.get('updated_by')
        instance.deleted_by = validated_data.get('deleted_by')
        instance.save()
        return instance


#:::::::::::::::::::::: T CORE Currency :::::::::::::::::::::::::::#
class CoreCurrencyAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    symbol = serializers.SerializerMethodField()

    class Meta:
        model = TCoreCurrency
        fields = '__all__'

    def get_symbol(self, obj):
        return eval(obj.symbol).decode() if obj.symbol else ''


class CoreCurrencyCreateSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreCurrency
        fields = '__all__'

    def create(self, validated_data):
        symbol = validated_data.pop('symbol', '').encode('utf-8')
        currency = TCoreCurrency.objects.create(**validated_data, symbol=symbol)
        return currency


class CoreCurrencyEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreCurrency
        fields = '__all__'

    def update(self, instance, validated_data):
        symbol = validated_data.pop('symbol','').encode('utf-8')
        TCoreCurrency.objects.filter(id=instance.id).update(**validated_data,symbol=symbol)
        return validated_data


class CoreCurrencyDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    deleted_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreCurrency
        fields = '__all__'

    def update(self, instance, validated_data):
        instance.is_deleted=True
        instance.updated_by = validated_data.get('updated_by')
        instance.deleted_by = validated_data.get('deleted_by')
        instance.save()
        return instance


#:::::::::::::::::::::: T CORE Domain :::::::::::::::::::::::::::#
class CoreDomainAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreDomain
        fields = '__all__'


class CoreDomainEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreDomain
        fields = '__all__'


class CoreDomainDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    deleted_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreDomain
        fields = '__all__'

    def update(self, instance, validated_data):
        instance.is_deleted=True
        instance.updated_by = validated_data.get('updated_by')
        instance.deleted_by = validated_data.get('deleted_by')
        instance.save()
        return instance


#:::::::::::::::::::::: T CORE CITY :::::::::::::::::::::::::::::#
class CoreCityAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TCoreCity
        fields = ('__all__')

    def create(self, validated_data):
        if validated_data.get('name'):
            if TCoreCity.objects.filter(name=validated_data.get('name')).count():
                raise APIException({'msg': 'City with this name already exists.',
                                    "request_status": 0})
            else:
                TCoreCity.objects.create(name=validated_data.get('name'), created_by=validated_data.get('created_by'))
                return validated_data
        else:
            raise APIException({'msg': ' You did not enter any  valid city name.',
                                "request_status": 0})



class CoreCityEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreCity
        fields = ('__all__')

class CoreCityDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    deleted_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TCoreCity
        fields = '__all__'

    def update(self, instance, validated_data):
        instance.is_deleted=True
        instance.updated_by = validated_data.get('updated_by')
        instance.deleted_by = validated_data.get('deleted_by')
        instance.save()
        return instance

class CoreCityListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TCoreCity
        fields = ('__all__')

class FloorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TCoreFloor
        fields = ('__all__')