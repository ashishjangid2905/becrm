from rest_framework import serializers
from .models import leads, contactPerson, Conversation, conversationDetails
from invoice.utils import STATE_CHOICE, COUNTRY_CHOICE
from teams.models import User
import uuid

class contactPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = contactPerson
        fields = ['id', 'person_name', 'email_id', 'contact_no', 'is_active']

class leadsSerializer(serializers.ModelSerializer):
    contactpersons = contactPersonSerializer(many=True, read_only=True)
    user = serializers.IntegerField(read_only=True)
    user_name = serializers.SerializerMethodField(read_only=True)
    uuid = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model= leads
        fields = [ 'id', 'uuid', 'company_name', 'gstin', 'full_address', 'address1', 'address2', 'city', 'state', 'country', 'pincode', 'industry', 'source', 'created_at', 'user', 'user_name', 'status', 'contactpersons']
    
    def get_user_name(self, obj):
        if obj.user:
            user_name = User.objects.get(pk=obj.user)
            return f'{user_name.first_name} {user_name.last_name}'
        else:
            return None
        
    def get_uuid(self, obj):
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(obj.id)))
    

class ConversationDetailsSerializer(serializers.ModelSerializer):
    person_name = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = conversationDetails
        fields = ['id', 'details', 'contact_person', 'person_name', 'status', 'follow_up', 'inserted_at', 'edited_at']

    def get_person_name(self, obj):
        return obj.contact_person.person_name


class ConversationSerializer(serializers.ModelSerializer):
    conversationdetails = ConversationDetailsSerializer(many=True)
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'company_id', 'conversationdetails','start_at']