#sing DRF we will be able to easily use a class serializer that will automatically serialize fields into JSON, and back to Python objects when needed

from rest_framework.serializers import ModelSerializer
from .models import CustomUser
class UserSerializer(ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('email', 'last_login', 'date_joined', 'is_staff')