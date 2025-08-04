from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from productos.models.usuario import SuperUsuario, PerfilUsuario, HistorialPuntos, Roles
from productos.models.configuracion import Barrio
import re
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = ['id', 'nombre']

class SuperUsuarioSerializer(serializers.ModelSerializer):
    barrio = serializers.PrimaryKeyRelatedField(queryset=Barrio.objects.all(), allow_null=True, required=False)
    rol = serializers.PrimaryKeyRelatedField(queryset=Roles.objects.all(), allow_null=True, required=False)

    class Meta:
        model = SuperUsuario
        fields = ['id', 'usuario', 'nombre','imagen', 'dni', 'telefono', 'barrio', 'domicilio', 'rol']

    def to_representation(self, instance):
        request = self.context.get('request')
        user = request.user if request else None
        if user and user.is_staff:
            return super().to_representation(instance)
        return {'nombre': instance.nombre}

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_username(self, value):
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{4,}$', value):
            raise serializers.ValidationError("El usuario debe tener letras y números, mínimo 4 caracteres.")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("El usuario ya existe.")
        return value

    def validate_email(self, value):
        if not re.match(r'^[^\s@]+@[^\s@]+\.(com|org|net|edu|gov|co|ar)$', value):
            raise serializers.ValidationError("El correo debe tener @ y una terminación válida.")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("El correo ya está registrado.")
        return value

    def validate_password(self, value):
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[A-Z])[A-Za-z\d]{8,}$', value):
            raise serializers.ValidationError("La contraseña debe tener al menos 8 caracteres, con letras, números y mayúsculas.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class PerfilUsuarioSerializer(serializers.ModelSerializer):
    barrio = serializers.PrimaryKeyRelatedField(queryset=Barrio.objects.all(), allow_null=True, required=False)

    class Meta:
        model = PerfilUsuario
        fields = '__all__'
        extra_kwargs = {'usuario': {'required': False}}

    def validate_nombre_apellido(self, value):
        if not value or len(value.split()) < 2:
            raise serializers.ValidationError("Debe ingresar al menos nombre y apellido.")
        return value

    def validate_dni(self, value):
        if not value or len(value) != 8 or not value.isdigit():
            raise serializers.ValidationError("El DNI debe tener exactamente 8 dígitos.")
        return value


class HistorialPuntosSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistorialPuntos
        fields = '__all__'


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        # Validar si el usuario existe
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise AuthenticationFailed(detail="Usuario no existente", code='authentication_failed')

        # Intentar autenticar al usuario
        user = authenticate(username=username, password=password)
        if user is None:
            raise AuthenticationFailed(detail="Contraseña incorrecta", code='authentication_failed')




        data = super().validate(attrs)

        if hasattr(self, 'user'):
            data['user'] = {
                'id': self.user.id,
                'username': self.user.username, 
                'email': self.user.email,
                'is_staff': self.user.is_staff,
            }
            refresh = RefreshToken.for_user(self.user)

            access_token = AccessToken.for_user(self.user)
            if self.user.is_staff:
                access_token_lifetime = timedelta(hours=12)
                logger.info(f"Admin detected, setting access token lifetime to: {access_token_lifetime}")
            else:
                access_token_lifetime = timedelta(minutes=60)
                logger.info(f"Non-admin user, setting access token lifetime to: {access_token_lifetime}")

            access_token.set_exp(lifetime=access_token_lifetime)

            data['access'] = str(access_token)
            data['refresh'] = str(refresh)

        return data


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()

