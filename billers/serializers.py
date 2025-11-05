from rest_framework import serializers
from billers.models import *

class BillerVariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillerVariable
        fields = ['id', 'variable_name', 'variable_value', 'from_date', 'to_date', 'inserted_by', 'Inserted_at']

class BillerSerializer(serializers.ModelSerializer):
    reg_full_address = serializers.SerializerMethodField(read_only = True)
    corp_full_address = serializers.SerializerMethodField(read_only = True)
    variables = BillerVariableSerializer(many = True, read_only=True)
    class Meta:
        model = Biller
        fields = '__all__'

    def get_reg_full_address(self, obj):
        address_parts = [
            obj.reg_address1,
            obj.reg_address2,
            obj.reg_city,
            obj.reg_pincode,
            obj.reg_state,
            obj.reg_country
        ]
        return ', '.join(filter(None, address_parts))
    
    def get_corp_full_address(self, obj):
        address_parts = [
            obj.corp_address1,
            obj.corp_address2,
            obj.corp_city,
            obj.corp_pincode,
            obj.corp_state,
            obj.corp_country
        ]
        return ', '.join(filter(None, address_parts))


class BankDetailSerializer(serializers.ModelSerializer):
    biller_name = serializers.SerializerMethodField()
    biller_gstin = serializers.SerializerMethodField()
    class Meta:
        model = BankDetail
        fields = '__all__'
        read_only_fields = ['biller_name', 'biller_gstin']

    def get_biller_name(self, obj):
        return obj.biller.biller_name
    
    def get_biller_gstin(self, obj):
        return obj.biller.biller_gstin
