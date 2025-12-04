from rest_framework.serializers import ModelSerializer

from .models import *

class BranchLabelSerializer(ModelSerializer):
    class Meta:
        model = BranchLabel
        fields = '__all__'