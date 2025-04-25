from rest_framework import serializers
from .models import sample, sample_no, CountryMaster, Portmaster

class SampleSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    class Meta:
        model = sample
        fields = '__all__'
        read_only_fields = ['sample_id', 'user', 'user_name']

    def get_user_name(self, obj):
        if obj.user:
            return f'{obj.user.first_name} {obj.user.last_name}'
        return None  # Handles cases where user might be null
    
class CountryMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryMaster
        fields = '__all__'

class PortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portmaster
        fields = '__all__'