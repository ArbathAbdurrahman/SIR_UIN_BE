from django.contrib.auth.models import User
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email tidak ditemukan.")
        return value
class UserSerializer(serializers.ModelSerializer):
    """
    Serializer untuk menampilkan data dasar pengguna.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', ]

class RegistrationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=30)
    
    email = serializers.CharField(
        max_length=100,
        validators=[UniqueValidator(
            queryset=User.objects.all(), 
            message="Email ini sudah terdaftar."
        )]
    )
    password1 = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name']

    def validate_username(self, value):
        # 1. Ubah ke format standar (lowercase, tanpa spasi)
        cleaned_username = value.replace(" ", "").lower()

        # 2. Validasi panjang karakter
        if len(cleaned_username) < 3:
            raise serializers.ValidationError("Username minimal harus 3 karakter.")
        if len(cleaned_username) > 30:
            raise serializers.ValidationError("Username maksimal 30 karakter.")

        # 3. Cek keunikan secara case-insensitive
        if User.objects.filter(username__iexact=cleaned_username).exists():
            raise serializers.ValidationError("Username ini sudah terdaftar.")
        
        return cleaned_username

    def validate_first_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Nama depan minimal 3 karakter.")
        if len(value) > 30:
            raise serializers.ValidationError("Nama depan maksimal 30 karakter.")
        return value

    def validate_last_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Nama belakang minimal 3 karakter.")
        if len(value) > 30:
            raise serializers.ValidationError("Nama belakang maksimal 30 karakter.")
        return value

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({"password2": "Konfirmasi password tidak cocok."})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password1'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        return user