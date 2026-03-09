from rest_framework import serializers
from apps.users.models import User

class UserRegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration, including email, password, first name, and last name."""
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        """Meta class for UserRegisterSerializer."""
        model = User
        fields = ("email", "password", "first_name", "last_name")

    def create(self, validated_data):
        """Create a new user instance with the provided validated data."""
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details, including id, email, first name, last name, and creation date."""
    class Meta:
        """Meta class for UserSerializer."""
        model = User
        fields = ("id", "email", "first_name", "last_name", "created_at")
    
class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login, accepting email and password."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    class Meta:
        """Meta class for UserLoginSerializer."""   
        fields = ("email", "password")

class UserLoginSuccessSerializer(serializers.Serializer):
    """Serializer for successful user login response, including email and JWT tokens."""
    email = serializers.EmailField()
    access = serializers.CharField()
    refresh = serializers.CharField()
    class Meta:
        """Meta class for UserLoginSuccessSerializer."""
        fields = ("email", "access", "refresh")