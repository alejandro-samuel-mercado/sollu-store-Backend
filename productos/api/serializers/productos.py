
from rest_framework import serializers
from productos.models.producto import Producto, Atributo,Marca,ProductoAtributo, ReviewProduct
from productos.models.categoria import Categoria, Descuento
from productos.services.producto_service import ProductoService
from django.conf import settings
from urllib.parse import urljoin
from django.db.models import Avg

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

    def update(self, instance, validated_data):
        if 'imagen' not in validated_data and instance.imagen:
            validated_data['imagen'] = instance.imagen
        return super().update(instance, validated_data)

class DescuentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Descuento
        fields = '__all__'

class AtributoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Atributo
        fields = ['id', 'nombre', 'valor']

class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = ['id', 'nombre']


class ProductoSimpleSerializer(serializers.ModelSerializer):
    precio_final = serializers.SerializerMethodField()
    descuento = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = ['id', 'nombre','categoria', 'imagen', 'imagen_secundaria', 'imagen_terciaria', 'precio_final', 'descuento']

    def get_precio_final(self, obj):
        return ProductoService.calcular_precio_final(obj)

    def get_descuento(self, obj):
        return ProductoService.obtener_descuento(obj)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.imagen:
            representation['imagen'] = urljoin(settings.MEDIA_URL, str(instance.imagen))
        if instance.imagen_secundaria:
            representation['imagen_secundaria'] = urljoin(settings.MEDIA_URL, str(instance.imagen_secundaria))
        if instance.imagen_terciaria:
            representation['imagen_terciaria'] = urljoin(settings.MEDIA_URL, str(instance.imagen_terciaria))
        return representation



class ReviewProductSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    product = serializers.PrimaryKeyRelatedField(queryset=Producto.objects.all())
    created_at = serializers.DateTimeField(read_only=True)
    approved = serializers.BooleanField(read_only=True)

    class Meta:
        model = ReviewProduct
        fields = ['id', 'user', 'product', 'comment', 'rating', 'approved', 'created_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['product'] = ProductoSimpleSerializer(instance.product).data
        return representation

class ProductoSerializer(serializers.ModelSerializer):
    precio_final = serializers.SerializerMethodField()
    descuento = serializers.SerializerMethodField()
    producto_atributos = serializers.SerializerMethodField()
    tipo = serializers.StringRelatedField()
    marca = serializers.StringRelatedField()
    categoria = serializers.StringRelatedField()
    stock_total = serializers.ReadOnlyField()
    cantidad_vendida_total = serializers.ReadOnlyField()
    reviews = ReviewProductSerializer(many=True, read_only=True)
    overall_rating = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            'id', 'tipo', 'marca', 'nombre', 'modelo_talle', 'descripcion', 'precio',
            'precio_final', 'descuento', 'valor_en_puntos', 'fecha_publicacion', 'imagen',
            'imagen_secundaria', 'imagen_terciaria', 'tendencia', 'categoria',
            'puntos_club_acumulables', 'qr_code', 'producto_atributos',
            'stock_total', 'cantidad_vendida_total','reviews', 'overall_rating'
        ]

    def get_producto_atributos(self, obj):
        return ProductoAtributoSerializer(obj.producto_atributos.all(), many=True).data
        
    def get_overall_rating(self, obj):
        reviews = obj.reviews.filter(approved=True)
        if not reviews.exists():
            return {"average_rating": 0, "total_reviews": 0}
        average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        total_reviews = reviews.count()
        return {
            "average_rating": round(average_rating, 1),
            "total_reviews": total_reviews
        }


    def update(self, instance, validated_data):
        if 'imagen' not in validated_data and instance.imagen:
            validated_data['imagen'] = instance.imagen
        return super().update(instance, validated_data)

    def get_precio_final(self, obj):
        return ProductoService.calcular_precio_final(obj)

    def get_descuento(self, obj):
        return ProductoService.obtener_descuento(obj)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.imagen:
            representation['imagen'] = urljoin(settings.MEDIA_URL, str(instance.imagen))
        if instance.imagen_secundaria:
            representation['imagen_secundaria'] = urljoin(settings.MEDIA_URL, str(instance.imagen_secundaria))
        if instance.imagen_terciaria:
            representation['imagen_terciaria'] = urljoin(settings.MEDIA_URL, str(instance.imagen_terciaria))
        if instance.qr_code:
            representation['qr_code'] = urljoin(settings.MEDIA_URL, str(instance.qr_code))
        else:
            representation['qr_code'] = None
        return representation

  

class ProductoAtributoSerializer(serializers.ModelSerializer):
    atributo = AtributoSerializer()
    producto = ProductoSimpleSerializer(read_only=True)
    class Meta:
        model = ProductoAtributo
        fields = ['id','producto', 'atributo', 'stock', 'cantidad_vendida', 'imagen']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.imagen:
            representation['imagen'] = urljoin(settings.MEDIA_URL, str(instance.imagen))
        return representation

