from rest_framework import status
from rest_framework.response import Response
from productos.models.venta import Venta, DetalleVenta, CarritoProducto, Carrito
from productos.models.producto import Producto
from productos.models.configuracion import PuntosClub
from productos.models.usuario import PerfilUsuario, HistorialPuntos
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class VentaService:
    @staticmethod
    def validate_venta_data(data, request):
        if not data.get('comprador') and not data.get('comprador_sin_cuenta') and not data.get('usuario_nuevo'):
            if request.user.is_authenticated:
                data['comprador'] = request.user
            else:
                raise ValueError("Se requiere un comprador.")
        if request.method == 'POST' and not data.get('detalles'):
            raise ValueError("El campo 'detalles' es requerido.")
        return data

    @staticmethod
    def create_venta(validated_data, request):
        with transaction.atomic():
            detalles_data = validated_data.pop('detalles')
            venta = Venta.objects.create(**validated_data)
            puntos_club_activo = PuntosClub.objects.first()
            puntos_acumulados = 0

            for detalle_data in detalles_data:
                producto_atributo = detalle_data['producto_atributo']
                cantidad = detalle_data['cantidad']
                producto_atributo.stock -= cantidad
                producto_atributo.cantidad_vendida += cantidad
                producto_atributo.save()
                DetalleVenta.objects.create(venta=venta, **detalle_data)

                if puntos_club_activo and puntos_club_activo.activo and producto_atributo.producto.puntos_club_acumulables:
                    puntos_acumulados += producto_atributo.producto.puntos_club_acumulables * cantidad

            if puntos_acumulados > 0 and venta.comprador:
                venta.puntos_club_acumulados = puntos_acumulados
                venta.save()
                perfil = PerfilUsuario.objects.get(usuario=venta.comprador)
                perfil.puntos_acumulados = (perfil.puntos_acumulados or 0) + puntos_acumulados
                perfil.save()
                HistorialPuntos.objects.create(
                    perfil=perfil,
                    puntos_obtenidos=puntos_acumulados,
                    descripcion=f"Puntos por compra (Venta #{venta.id})"
                )
            return venta

    @staticmethod
    def agregar_producto_al_carrito(request):
        usuario = request.user
        producto_atributo_id = request.data.get('producto_atributo_id')
        cantidad = int(request.data.get('cantidad', 1))

        producto_atributo = ProductoAtributo.objects.get(id=producto_atributo_id)
        if producto_atributo.stock < cantidad:
            return Response({'error': 'Stock insuficiente'}, status=status.HTTP_400_BAD_REQUEST)

        carrito, _ = Carrito.objects.get_or_create(usuario=usuario)
        producto_carrito, created = CarritoProducto.objects.get_or_create(
            carrito=carrito, producto_atributo=producto_atributo, defaults={'cantidad': cantidad}
        )
        if not created:
            producto_carrito.cantidad += cantidad
            producto_carrito.save()
        return Response({'message': 'Producto agregado al carrito'}, status=status.HTTP_200_OK)


    @staticmethod
    def eliminar_producto_del_carrito(request):
        usuario = request.user
        producto_atributo_id = request.data.get('producto_atributo_id')
        carrito = Carrito.objects.get(usuario=usuario)
        producto_carrito = CarritoProducto.objects.get(carrito=carrito, producto_atributo_id=producto_atributo_id)
        producto_carrito.delete()
        return Response({'message': 'Producto eliminado del carrito'}, status=status.HTTP_200_OK)

    @staticmethod
    def crear_venta_api(request):
        from productos.api.serializers.ventas import VentaSerializer
        serializer = VentaSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        venta = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)