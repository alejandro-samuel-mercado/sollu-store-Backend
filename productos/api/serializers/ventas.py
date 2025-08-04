from rest_framework import serializers
from productos.models.venta import Venta, DetalleVenta, Carrito, CarritoProducto, EstadosVenta
from productos.models.usuario import PerfilUsuario,HistorialPuntos
from productos.models.configuracion import Envio, Barrio,Cupon,PuntosClub
from productos.services.venta_service import VentaService
from .usuarios import UserRegisterSerializer, PerfilUsuarioSerializer
from .productos import ProductoSimpleSerializer,ProductoAtributoSerializer
from productos.models.producto import Producto,ProductoAtributo
import logging
logger = logging.getLogger(__name__)


class CarritoProductoSerializer(serializers.ModelSerializer):
    producto_atributo = ProductoAtributoSerializer(read_only=True)
    producto_atributo_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductoAtributo.objects.all(),
        source='producto_atributo',
        write_only=True
    )

    class Meta:
        model = CarritoProducto
        fields = ['id', 'producto_atributo', 'producto_atributo_id', 'cantidad']

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0.")
        return value

    def validate(self, data):
        producto_atributo = data.get('producto_atributo')
        cantidad = data.get('cantidad')
        if producto_atributo and cantidad > producto_atributo.stock:
            raise serializers.ValidationError({
                'cantidad': f"No hay suficiente stock. Stock disponible: {producto_atributo.stock}"
            })
        return data

class CarritoSerializer(serializers.ModelSerializer):
    productos = CarritoProductoSerializer(many=True, read_only=True)

    class Meta:
        model = Carrito
        fields = ['id', 'usuario', 'productos']


class DetalleVentaSerializer(serializers.ModelSerializer):
    producto_atributo = ProductoAtributoSerializer(read_only=True)
    producto_atributo_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductoAtributo.objects.all(),
        source='producto_atributo',
        write_only=True
    )

    class Meta:
        model = DetalleVenta
        fields = ['producto_atributo', 'producto_atributo_id', 'cantidad', 'precio_unitario', 'subtotal']

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0.")
        return value


class EstadosVentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadosVenta
        fields = ['id', 'estado']

class VentaSerializer(serializers.ModelSerializer):
    detalles = DetalleVentaSerializer(many=True)
    tipo_envio = serializers.PrimaryKeyRelatedField(queryset=Envio.objects.all(), allow_null=True, required=False)
    barrio = serializers.PrimaryKeyRelatedField(queryset=Barrio.objects.all(), allow_null=True, required=False)
    puntos_club_acumulados = serializers.IntegerField(read_only=True)
    usuario_nuevo = UserRegisterSerializer(required=False)
    perfil_usuario = PerfilUsuarioSerializer(required=False)
    estado = serializers.PrimaryKeyRelatedField(
        queryset=EstadosVenta.objects.all(), required=False
    )
    estado_detail = EstadosVentaSerializer(source="estado", read_only=True)

    class Meta:
        model = Venta
        fields = [
            'id', 'comprador', 'comprador_sin_cuenta', 'vendedor', 'fecha_venta', 'precio_total', 'barrio',
            'tipo_envio', 'domicilio', 'fecha_entrega', 'horario_entrega', 'detalles', 'puntos_club_acumulados',
            'usuario_nuevo', 'perfil_usuario', 'estado', 'estado_detail', 'comprobante_pdf',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.precio_total is not None:
            data['precio_total'] = str(instance.precio_total)
        return data

    def validate_estado(self, value):
        logger.info(f"Validando estado: {value}")
        return value

    def validate(self, data):
        logger.info("Datos crudos recibidos en validate: %s", data)

        if not data.get('comprador') and not data.get('comprador_sin_cuenta') and not data.get('usuario_nuevo'):
            if self.context['request'].user.is_authenticated:
                data['comprador'] = self.context['request'].user
            else:
                raise serializers.ValidationError(
                    "Se requiere un comprador, comprador_sin_cuenta o usuario_nuevo."
                )

        if data.get('usuario_nuevo') and not data.get('perfil_usuario'):
            raise serializers.ValidationError(
                "Se requiere 'perfil_usuario' si se proporciona 'usuario_nuevo'."
            )

        if self.context['request'].method == 'POST' and not data.get('detalles'):
            raise serializers.ValidationError("El campo 'detalles' es requerido.")

        if 'barrio' in data and data['barrio'] is not None:
            if isinstance(data['barrio'], Barrio):
                data['barrio'] = data['barrio'].id
            elif not isinstance(data['barrio'], (int, str)):
                raise serializers.ValidationError(
                    {'barrio': "El valor de 'barrio' debe ser un ID válido."}
                )
            else:
                try:
                    data['barrio'] = int(data['barrio'])
                except (ValueError, TypeError):
                    raise serializers.ValidationError(
                        {'barrio': "El valor de 'barrio' debe ser un ID válido."}
                    )

        logger.info("Datos validados en validate: %s", data)
        return data

    def update(self, instance, validated_data):
        logger.info("Datos validados recibidos en update: %s", validated_data)
        if "estado" in validated_data:
            instance.estado = validated_data.pop("estado")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def create(self, validated_data):
        logger.info("Validated data en create: %s", validated_data)
        detalles_data = validated_data.pop('detalles')
        usuario_nuevo_data = validated_data.pop('usuario_nuevo', None)
        perfil_usuario_data = validated_data.pop('perfil_usuario', None)

        if usuario_nuevo_data and perfil_usuario_data:
            user_serializer = UserRegisterSerializer(data=usuario_nuevo_data)
            if user_serializer.is_valid(raise_exception=True):
                user = user_serializer.save()
                if 'barrio' in perfil_usuario_data and perfil_usuario_data['barrio'] is not None:
                    if isinstance(perfil_usuario_data['barrio'], Barrio):
                        perfil_usuario_data['barrio'] = perfil_usuario_data['barrio'].id
                    elif isinstance(perfil_usuario_data['barrio'], str):
                        perfil_usuario_data['barrio'] = int(perfil_usuario_data['barrio'])
                perfil, created = PerfilUsuario.objects.get_or_create(usuario=user)
                if not created:
                    perfil_serializer = PerfilUsuarioSerializer(perfil, data=perfil_usuario_data, partial=True)
                    if perfil_serializer.is_valid(raise_exception=True):
                        perfil_serializer.save()
                else:
                    perfil_serializer = PerfilUsuarioSerializer(perfil, data=perfil_usuario_data, partial=True)
                    if perfil_serializer.is_valid(raise_exception=True):
                        perfil_serializer.save()
                validated_data['comprador'] = user

        if not validated_data.get('comprador') and not validated_data.get('comprador_sin_cuenta'):
            if self.context['request'].user.is_authenticated:
                validated_data['comprador'] = self.context['request'].user
            else:
                raise serializers.ValidationError("No se especificó un comprador válido")

        if not validated_data.get('domicilio') and validated_data.get('comprador'):
            perfil = PerfilUsuario.objects.filter(usuario=validated_data['comprador']).first()
            if perfil:
                validated_data['domicilio'] = validated_data.get('domicilio', perfil.domicilio)

        if 'barrio' in validated_data and validated_data['barrio'] is not None:
            validated_data['barrio'] = Barrio.objects.get(id=validated_data['barrio'])

        venta = Venta.objects.create(**validated_data)

        puntos_club_activo = PuntosClub.objects.first()
        puntos_acumulados = 0

        for detalle_data in detalles_data:
            producto_atributo = detalle_data['producto_atributo']
            cantidad = detalle_data['cantidad']

            producto_atributo.stock -= cantidad
            producto_atributo.cantidad_vendida = (producto_atributo.cantidad_vendida or 0) + cantidad
            producto_atributo.save()

            DetalleVenta.objects.create(
                venta=venta,
                producto_atributo=producto_atributo,
                cantidad=cantidad,
                precio_unitario=detalle_data['precio_unitario'],
                subtotal=detalle_data['subtotal']
            )

            if puntos_club_activo and puntos_club_activo.activo and producto.puntos_club_acumulables:
                puntos_acumulados += producto.puntos_club_acumulables * cantidad

        if puntos_acumulados > 0 and venta.comprador:
            venta.puntos_club_acumulados = puntos_acumulados
            venta.save()
            perfil = PerfilUsuario.objects.get(usuario=venta.comprador)
            puntos_anteriores = perfil.puntos_acumulados or 0
            nuevos_puntos = puntos_anteriores + puntos_acumulados
            PerfilUsuario.objects.filter(id=perfil.id).update(puntos_acumulados=nuevos_puntos)
            perfil.refresh_from_db()

            HistorialPuntos.objects.create(
                perfil=perfil,
                puntos_obtenidos=puntos_acumulados,
                descripcion=f"Puntos obtenidos por compra (Venta #{venta.id})"
            )

        return venta