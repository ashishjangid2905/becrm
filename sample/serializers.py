from rest_framework import serializers
from .models import sample, sample_no

class SampleSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    class Meta:
        model = sample
        fields = '__all__'
        read_only_fields = ['user', 'user_name']

    def get_user_name(self, obj):
        return f'{obj.user.first_name} {obj.user.last_name}'