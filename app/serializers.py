from rest_framework import serializers
from invoice.models import proforma
from invoice.custom_utils import sale_category, total_order_value
from invoice.serializers import BankDetailSerializer


class DashboardSaleSerializer(serializers.ModelSerializer):
    totalValue = serializers.SerializerMethodField(read_only = True)
    category_sales = serializers.SerializerMethodField(read_only = True)
    bank = BankDetailSerializer()
    class Meta:
        model = proforma
        fields = ['user_id', 'user_name', 'pi_no', 'pi_date', 'totalValue', 'category_sales', 'closed_at', 'bank', 'status']
        read_only_fields = ['user_id', 'user_name', 'pi_no', 'pi_date', 'totalValue', 'category_sales', 'closed_at', 'bank', 'status']

    def get_totalValue(self,obj):
        try:
            return total_order_value(obj.id)
        except:
            print("error")

    def get_category_sales(self, obj):
        try:
            return sale_category(obj.id)
        except:
            print("error")