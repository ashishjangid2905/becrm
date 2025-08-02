from rest_framework import serializers
from .models import *
from teams.models import User
from django.db import transaction
from .custom_utils import total_pi_value_inc_tax, sale_category, pi_number, total_lumpsums, update_or_create_summery
from billers.serializers import *


class OrderListSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    class Meta:
        model = orderList
        fields = ['id', 'category', 'report_type', 'country', 'product', 'from_month', 'to_month', 'unit_price', 'total_price', 'lumpsum_amt', 'is_lumpsum', 'order_status', 'inserted_at', 'updated_at']

class ConvertedPISerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    class Meta:
        model = convertedPI
        fields = '__all__'
        # read_only_fields = ['pi_id']

class ProcessedOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = processedOrder
        fields = '__all__'
        read_only_fields = ['pi_id']

class PiSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = PiSummary
        fields = '__all__'


class ProformaSerializer(serializers.ModelSerializer):
    orderlist = OrderListSerializer(many=True)
    convertedpi = ConvertedPISerializer(many=False, read_only = True)
    processedorders = ProcessedOrderSerializer(many=True, read_only = True)
    bank = BankDetailSerializer(many=False)
    totalLumpsum = serializers.SerializerMethodField(read_only=True)
    summary = PiSummarySerializer()
    approved_sign = serializers.SerializerMethodField(read_only = True)
    class Meta:
        model = proforma
        # fields = ['id', 'company_ref', 'user_id', 'user_name', 'user_contact', 'user_email', 'company_name', 'gstin', 'is_sez', 'lut_no', 'vendor_code', 'address', 'country', 'state', 'requistioner', 'email_id', 'contact', 'pi_no', 'pi_date', 'po_no', 'po_date', 'subscription', 'payment_term', 'bank', 'currency', 'details', 'is_Approved', 'approved_by', 'approved_sign', 'approved_at', 'status', 'closed_at', 'created_at', 'edited_by', 'edited_at', 'slug', 'feedback', 'additional_email', 'totalValue', 'totalValue_incTax', 'category_sales', 'orderlist', 'convertedpi', 'processedorders']
        fields = '__all__'
        
    def get_totalLumpsum(self, obj):
        try:
            return total_lumpsums(int(obj.id))
        except:
            print(f"Debug: obj = {obj} and obj.id = {obj.id}")

    def get_approved_sign(self, obj):
        if obj.approved_by:
            sign = User.objects.get(pk=obj.approved_by)
            return f'{sign.first_name} {sign.last_name}'
        return ""
    
class ProformaCreateSerializer(serializers.ModelSerializer):
    orderlist = OrderListSerializer(many =True)
    class Meta:
        model = proforma
        fields = '__all__'
        read_only_fields = ['user_id', 'pi_no']

    @transaction.atomic
    def create(self, validated_data):
        order_data = validated_data.pop("orderlist", [])
        if not order_data:
            raise serializers.ValidationError({"orderlist": "Order list cannot be empty."})
        bank_instance = validated_data.get("bank")
        pi_no = pi_number(bank_instance.biller_id)
        validated_data["pi_no"] = pi_no
        try:
            proforma_instance = proforma.objects.create(**validated_data)

            order_instances = [
                orderList(proforma_id=proforma_instance, **order) for order in order_data
            ]

            orderList.objects.bulk_create(order_instances)
            update_or_create_summery(proforma_instance)

            return proforma_instance
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})
        
    def update(self, instance, validated_data):
        order_data = validated_data.pop("orderlist", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if order_data is not None:
            with transaction.atomic():
                # fetching existing orders list
                existing_orders = {order.id: order for order in instance.orderlist.all()}

                # List for batch oprations
                updated_orders = []
                new_orders = []
                # incoming orders
                for order in order_data:
                    order_id = order.get("id")
                    if order_id and int(order_id) in existing_orders:
                        existing_order = existing_orders[order_id]

                        for key, value in order.items():
                            setattr(existing_order, key, value)
                        updated_orders.append(existing_order)
                    else:
                        new_orders.append(orderList(proforma_id=instance, **order))
                if updated_orders:
                    orderList.objects.bulk_update(updated_orders, fields=[  # Only update relevant fields
                    "category", "report_type", "country", "product", "from_month", "to_month",
                    "unit_price", "total_price", "lumpsum_amt", "is_lumpsum", "order_status"
                    ])

                existing_order_ids = {int(order["id"]) for order in order_data if "id" in order}
                instance.orderlist.exclude(id__in = existing_order_ids).delete()

                if new_orders:
                    orderList.objects.bulk_create(new_orders)
                
        update_or_create_summery(instance)

        return instance

        