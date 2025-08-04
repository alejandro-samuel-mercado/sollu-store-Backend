from django.db import models
from django.contrib.auth.models import User
from productos.models.producto import Producto,ProductoAtributo
from productos.models.configuracion import Barrio, Envio
from storages.backends.s3boto3 import S3Boto3Storage
from django.db.models import JSONField

class EstadosVenta(models.Model):
    estado = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Estado #{self.id} - {self.estado}"

class Venta(models.Model):
    comprador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ventas', null=True, blank=True)
    comprador_sin_cuenta = models.CharField(max_length=100, null=True, blank=True, default="---")
    vendedor = models.ForeignKey('SuperUsuario', on_delete=models.CASCADE, null=True, blank=True)
    puntos_club_acumulados = models.IntegerField(blank=True, null=True)
    fecha_venta = models.DateTimeField(auto_now_add=True)
    precio_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    barrio = models.ForeignKey(Barrio, on_delete=models.SET_NULL, null=True, blank=True)
    tipo_envio = models.ForeignKey(Envio, on_delete=models.SET_NULL, null=True, blank=True)
    domicilio = models.CharField(max_length=255, blank=True, null=True)
    fecha_entrega = models.DateField(blank=True, null=True)
    horario_entrega = models.CharField(max_length=50, blank=True, null=True)
    estado = models.ForeignKey(EstadosVenta, on_delete=models.SET_NULL, null=True, blank=True)
    comprobante_pdf = models.FileField(storage=S3Boto3Storage(), upload_to='comprobantes/', null=True, blank=True)

    def __str__(self):
        return f"Venta #{self.id} - {self.fecha_venta.strftime('%d/%m/%Y')}"

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles', null=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, null=True, blank=True)
    combinacion = JSONField(default=list)  
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        combinacion_str = ", ".join(f"{item['tipo']}:{item['valor']}" for item in self.combinacion)
        return f"{self.cantidad} x {self.producto.nombre} ({combinacion_str}) en Venta #{self.venta.id}"

class Carrito(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Carrito de {self.usuario.username}"


class CarritoProducto(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='productos')
    producto_atributo = models.ForeignKey(ProductoAtributo, on_delete=models.CASCADE,null=True)
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        #producto_nombre = self.producto_atributo.producto.nombre if self.producto_atributo.producto else "Sin Nombre"
        return f"{self.cantidad} x () en el carrito de {self.carrito.usuario.username}"

    class Meta:
        unique_together = ['carrito', 'producto_atributo']

class Pago(models.Model):
    nombre = models.CharField(max_length=255)
    email = models.EmailField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default="pending")
    mp_payment_id = models.CharField(max_length=100, null=True, blank=True)
    mp_status_detail = models.TextField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.monto} - {self.status}"