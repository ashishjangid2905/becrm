from rest_framework import serializers
from invoice.models import proforma
from invoice.custom_utils import sale_category, total_order_value
from invoice.serializers import BankDetailSerializer, PiSummarySerializer


class DashboardSaleSerializer(serializers.ModelSerializer):
    summary = PiSummarySerializer(read_only=True)
    bank = BankDetailSerializer()
    class Meta:
        model = proforma
        fields = ['user_id', 'user_name', 'pi_no', 'pi_date', 'summary', 'closed_at', 'bank', 'status']
        read_only_fields = ['user_id', 'user_name', 'pi_no', 'pi_date', 'summary', 'closed_at', 'bank', 'status']