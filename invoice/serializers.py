from rest_framework import serializers
from .models import proforma, orderList, convertedPI, processedOrder, bankDetail, biller, BillerVariable

class BillerVariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillerVariable
        fields = ['id', 'variable_name', 'variable_value', 'from_date', 'to_date', 'inserted_by', 'Inserted_at']

class BillerSerializer(serializers.ModelSerializer):
    reg_full_address = serializers.SerializerMethodField(read_only = True)
    corp_full_address = serializers.SerializerMethodField(read_only = True)
    variables = BillerVariableSerializer(many = True)
    class Meta:
        model = biller
        fields = ['biller_name', 'brand_name', 'biller_gstin', 'biller_pan', 'biller_msme', 'reg_address1', 'reg_address2', 'reg_city', 'reg_state', 'reg_pincode', 'reg_country', 'corp_address1', 'corp_address2', 'corp_city', 'corp_state', 'corp_pincode', 'corp_country', 'reg_full_address', 'corp_full_address' 'inserted_at', 'edited_at', 'inserted_by', 'variables']

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
    class Meta:
        model = bankDetail
        fields = '__all__'


class OrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = orderList
        fields = ['id', 'category', 'report_type', 'product', 'from_month', 'to_month', 'unit_price', 'total_price', 'lumpsum_amt', 'is_lumpsum', 'order_status', 'inserted_at', 'updated_at']

class PerformaSerializer(serializers.ModelSerializer):
    orderlist = OrderListSerializer(many=True)
    pi_no = serializers.CharField(read_only = True)
    slug = serializers.SlugField(read_only = True)
    bank = BankDetailSerializer(many=False)

    class Meta:
        model = proforma
        fields = ['id', 'company_ref', 'user_id', 'user_name', 'user_contact', 'user_email', 'company_name', 'gstin', 'is_sez', 'lut_no', 'vendor_code', 'address', 'country', 'state', 'requistioner', 'email_id', 'contact', 'pi_no', 'pi_date', 'po_no', 'po_date', 'subscription', 'payment_term', 'bank', 'currency', 'details', 'is_Approved', 'approved_by', 'approved_at', 'status', 'closed_at', 'created_at', 'edited_by', 'edited_at', 'slug', 'feedback', 'additional_email', 'orderlist']
