from django.db import models
from django.contrib.auth.models import User
from productos.models.configuracion import Barrio
from productos.models.producto import Producto,ProductoAtributo
from storages.backends.s3boto3 import S3Boto3Storage
from django.db.models import JSONField

class Roles(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return f"Rol {self.nombre}"

class SuperUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=100, null=True, blank=True)
    imagen = models.ImageField(storage=S3Boto3Storage(), upload_to='usuarios/', null=True, blank=True)
    dni = models.CharField(max_length=20, unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    barrio = models.ForeignKey(Barrio, on_delete=models.SET_NULL, null=True, blank=True)
    domicilio = models.TextField(null=True, blank=True)
    rol = models.ForeignKey(Roles, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        rol_nombre = self.rol.nombre if self.rol else "Sin rol"
        return f"{self.nombre} - {rol_nombre}"


class PerfilUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    nombre_apellido = models.CharField(max_length=100, null=True, blank=True)
    imagen = models.ImageField(storage=S3Boto3Storage(), upload_to='usuarios/', null=True, blank=True)
    dni = models.CharField(max_length=20, unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    pais = models.CharField(max_length=50, null=True, blank=True)
    barrio = models.ForeignKey(Barrio, on_delete=models.SET_NULL, null=True, blank=True)
    domicilio = models.TextField(null=True, blank=True)
    puntos_acumulados = models.PositiveIntegerField(blank=True, null=True, default=0)
    favoritos = models.ManyToManyField(ProductoAtributo, related_name='favoritos_de_usuarios', blank=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.puntos_acumulados} puntos"


class HistorialPuntos(models.Model):
    perfil = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE, related_name='historial')
    puntos_obtenidos = models.IntegerField()
    descripcion = models.CharField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.perfil.usuario.username} - {self.puntos_obtenidos} puntos el {self.fecha.strftime('%d/%m/%Y')}"

class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"Código {self.code} para {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = datetime.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)
