from rest_framework import serializers
from .models import proforma, orderList, convertedPI, processedOrder, bankDetail, biller, BillerVariable
from teams.models import User

from .custom_utils import total_pi_value_inc_tax, sale_category

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
    biller_name = serializers.SerializerMethodField()
    class Meta:
        model = bankDetail
        fields = '__all__'
        read_only_fields = ['biller_name']

    def get_biller_name(self, obj):
        return obj.biller_id.biller_name


class OrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = orderList
        fields = ['id', 'category', 'report_type', 'product', 'from_month', 'to_month', 'unit_price', 'total_price', 'lumpsum_amt', 'is_lumpsum', 'order_status', 'inserted_at', 'updated_at']

class ConvertedPISerializer(serializers.ModelSerializer):
    class Meta:
        model = convertedPI
        fields = '__all__'
        read_only_fields = ['pi_id']

class ProcessedOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = processedOrder
        fields = '__all__'
        read_only_fields = ['pi_id']

class ProformaSerializer(serializers.ModelSerializer):
    orderlist = OrderListSerializer(many=True)
    convertedpi = ConvertedPISerializer(many=False, read_only = True)
    processedorders = ProcessedOrderSerializer(many=True, read_only = True)
    pi_no = serializers.CharField(read_only = True)
    slug = serializers.SlugField(read_only = True)
    bank = BankDetailSerializer(many=False)
    totalValue = serializers.SerializerMethodField(read_only = True)
    totalValue_incTax = serializers.SerializerMethodField(read_only = True)
    category_sales = serializers.SerializerMethodField(read_only = True)
    approved_sign = serializers.SerializerMethodField(read_only = True)
    class Meta:
        model = proforma
        fields = ['id', 'company_ref', 'user_id', 'user_name', 'user_contact', 'user_email', 'company_name', 'gstin', 'is_sez', 'lut_no', 'vendor_code', 'address', 'country', 'state', 'requistioner', 'email_id', 'contact', 'pi_no', 'pi_date', 'po_no', 'po_date', 'subscription', 'payment_term', 'bank', 'currency', 'details', 'is_Approved', 'approved_by', 'approved_sign', 'approved_at', 'status', 'closed_at', 'created_at', 'edited_by', 'edited_at', 'slug', 'feedback', 'additional_email', 'totalValue', 'totalValue_incTax', 'category_sales', 'orderlist', 'convertedpi', 'processedorders']

    def get_totalValue(self, obj):
        total_sum = 0
        unique_lumpsum_amt = set()
        for order in obj.orderlist.all():
            if order.is_lumpsum and order.lumpsum_amt:
                unique_lumpsum_amt.add(order.lumpsum_amt)
            elif not order.is_lumpsum:
                total_sum += order.total_price
        total_sum+=sum(unique_lumpsum_amt)
        return total_sum

    def get_totalValue_incTax(self, obj):
        try:
            return total_pi_value_inc_tax(int(obj.id))
        except:
            print(f"Debug: obj = {obj} and obj.id = {obj.id}")

    def get_category_sales(self, obj):
        try:
            return sale_category(obj.id)
        except:
            print("error")

    def get_approved_sign(self, obj):
        if obj.approved_by:
            sign = User.objects.get(pk=obj.approved_by)
            return f'{sign.first_name} {sign.last_name}'
        return ""