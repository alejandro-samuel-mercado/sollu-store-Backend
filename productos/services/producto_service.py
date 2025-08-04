from decimal import Decimal
from productos.models.producto import Producto
from productos.models.categoria import Descuento

class ProductoService:
    @staticmethod
    def calcular_precio_final(producto: Producto) -> Decimal:
        precio_final = producto.precio
        descuento_aplicado = Decimal(0)

        if producto.descuento is not None and producto.descuento > 0:
            descuento_aplicado = producto.descuento
        else:
            descuento = Descuento.objects.filter(categoria=producto.categoria).first()
            if descuento and descuento.porcentaje:
                descuento_aplicado = descuento.porcentaje

        if descuento_aplicado > 0:
            precio_final -= (precio_final * (descuento_aplicado / Decimal(100)))

        return round(precio_final, 2)

    @staticmethod
    def obtener_descuento(producto: Producto) -> int:
        if producto.descuento is not None and producto.descuento > 0:
            return round(producto.descuento, 0)
        descuento = Descuento.objects.filter(categoria=producto.categoria).first()
        porcentaje = descuento.porcentaje if descuento else 0
        return round(porcentaje, 0)