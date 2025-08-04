from rest_framework import serializers
from productos.models.configuracion import (
    Review, Componentes_Configuraciones, Color, Tema, ContenidosWeb,
    InformacionWeb, Fuente, FuenteAplicar, PuntosClub, Diseños,Cupon,Barrio,Envio
)


class EnvioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Envio
        fields = '__all__'

class BarrioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barrio
        fields = '__all__'

class CuponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cupon
        fields = ['id', 'codigo', 'descuento', 'fecha_expiracion']

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    approved = serializers.BooleanField(read_only=True)
    class Meta:
        model = Review
        fields = ['id', 'user', 'comment', 'rating', 'approved', 'created_at']


class Componentes_ConfiguracionesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Componentes_Configuraciones
        fields = "__all__"

class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = '__all__'

class FuenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fuente
        fields = '__all__'

class FuenteAplicarSerializer(serializers.ModelSerializer):
    fuente = FuenteSerializer()
    color = ColorSerializer()

    class Meta:
        model = FuenteAplicar
        fields = ['id', 'fuente', 'color']

class TemaSerializer(serializers.ModelSerializer):
    primario1 = serializers.PrimaryKeyRelatedField(queryset=Color.objects.all())
    primario2 = serializers.PrimaryKeyRelatedField(queryset=Color.objects.all())
    secundario1 = serializers.PrimaryKeyRelatedField(queryset=Color.objects.all())
    secundario2 = serializers.PrimaryKeyRelatedField(queryset=Color.objects.all())
    terciario = serializers.PrimaryKeyRelatedField(queryset=Color.objects.all())
    cuarto = serializers.PrimaryKeyRelatedField(queryset=Color.objects.all())
    fondo1 = serializers.PrimaryKeyRelatedField(queryset=Color.objects.all())
    fondo2 = serializers.PrimaryKeyRelatedField(queryset=Color.objects.all())
    fondo3 = serializers.PrimaryKeyRelatedField(queryset=Color.objects.all())
    fondo4 = serializers.PrimaryKeyRelatedField(queryset=Color.objects.all())
    fondo5 = serializers.PrimaryKeyRelatedField(queryset=Color.objects.all())
    fuente_primaria = serializers.PrimaryKeyRelatedField(queryset=FuenteAplicar.objects.all(), allow_null=True)
    fuente_secundaria = serializers.PrimaryKeyRelatedField(queryset=FuenteAplicar.objects.all(), allow_null=True)
    fuente_terciaria = serializers.PrimaryKeyRelatedField(queryset=FuenteAplicar.objects.all(), allow_null=True)

    class Meta:
        model = Tema
        fields = [
            'id', 'titulo', 'primario1', 'primario2', 'secundario1', 'secundario2',
            'terciario', 'cuarto', 'fondo1', 'fondo2', 'fondo3', 'fondo4', 'fondo5',
            'fuente_primaria', 'fuente_secundaria', 'fuente_terciaria', 'activo'
        ]

class ContenidosWebSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContenidosWeb
        fields = '__all__'

    def update(self, instance, validated_data):
        if 'imagen' not in validated_data and instance.imagen:
            validated_data['imagen'] = instance.imagen
        return super().update(instance, validated_data)

class InformacionWebSerializer(serializers.ModelSerializer):
    class Meta:
        model = InformacionWeb
        fields = '__all__'

    def update(self, instance, validated_data):
        if 'imagen' not in validated_data and instance.imagen:
            validated_data['imagen'] = instance.imagen
        return super().update(instance, validated_data)

class PuntosClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = PuntosClub
        fields = ['id', 'activo']

class DiseñosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diseños
        fields = '__all__'