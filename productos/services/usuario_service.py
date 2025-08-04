
from django.contrib.auth.models import User
from productos.models.usuarios import PerfilUsuario 
from productos.api.serializers.usuarios import UserRegisterSerializer, PerfilUsuarioSerializer
from rest_framework import serializers
import re


class UsuarioService:
    @staticmethod
    def registrar_usuario(data):
        serializer = UserRegisterSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return user

    @staticmethod
    def crear_perfil_usuario(user, data):
        perfil_data = {
            'usuario': user.id,
            'nombre_apellido': data.get('nombre_apellido'),
            'dni': data.get('dni'),
            'telefono': data.get('telefono'),
            'barrio': data.get('barrio'),
            'domicilio': data.get('domicilio'),
        }
        serializer = PerfilUsuarioSerializer(data=perfil_data)
        serializer.is_valid(raise_exception=True)
        perfil = serializer.save()
        return perfil

    @staticmethod
    def actualizar_perfil_usuario(perfil, data):
        serializer = PerfilUsuarioSerializer(perfil, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        perfil = serializer.save()
        return perfil