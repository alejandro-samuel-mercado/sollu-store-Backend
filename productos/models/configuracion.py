from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage

class Envio(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre

class Barrio(models.Model):
    nombre = models.CharField(max_length=50)
    precio = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return self.nombre

class Review(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='reviews')
    comment = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reseña de {self.user.username} - {self.rating} estrellas"

class Cupon(models.Model):
    codigo = models.CharField(max_length=50)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fecha_expiracion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.codigo
 

class Componentes_Configuraciones(models.Model):
    componente_reseñas = models.BooleanField(default=True)
    componente_anuncios = models.BooleanField(default=True)
    componente_tendencia = models.BooleanField(default=True)
    componente_varios = models.BooleanField(default=True)
    componente_carrito_animado = models.BooleanField(default=True)
    componente_sonido = models.BooleanField(default=True)
    componente_categoria = models.BooleanField(default=True)
    componente_canjes = models.BooleanField(default=True)
    componente_probarProducto = models.BooleanField(default=True)

class Color(models.Model):
    nombre = models.CharField(max_length=50)
    codigo_hex = models.CharField(max_length=15, help_text="Código hexadecimal del color")

    def __str__(self):
        return f"{self.nombre} ({self.codigo_hex})"

class Fuente(models.Model):
    nombre = models.CharField(max_length=100, null=True, blank=True)
    activo = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre}"

class FuenteAplicar(models.Model):
    fuente = models.ForeignKey(Fuente, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.fuente} - {self.color}"

class Tema(models.Model):
    titulo = models.CharField(max_length=100)
    primario1 = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, related_name='primario1')
    primario2 = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, related_name='primario2')
    secundario1 = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, related_name='secundario1')
    secundario2 = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, related_name='secundario2')
    terciario = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, related_name='terciario')
    cuarto = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, related_name='cuarto')
    fondo1 = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, related_name='fondo1')
    fondo2 = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, related_name='fondo2')
    fondo3 = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, related_name='fondo3')
    fondo4 = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, related_name='fondo4')
    fondo5 = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, related_name='fondo5')
    fuente_primaria = models.ForeignKey(FuenteAplicar, null=True, blank=True, on_delete=models.SET_NULL, related_name='temas_primaria')
    fuente_secundaria = models.ForeignKey(FuenteAplicar, null=True, blank=True, on_delete=models.SET_NULL, related_name='temas_secundaria')
    fuente_terciaria = models.ForeignKey(FuenteAplicar, null=True, blank=True, on_delete=models.SET_NULL, related_name='temas_terciaria')
    activo = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.titulo}- {self.activo}"

class ContenidosWeb(models.Model):
    nombre = models.CharField(max_length=50, blank=True, null=True)
    contenido = models.TextField(null=True, blank=True)
    imagen = models.ImageField(storage=S3Boto3Storage(), upload_to='contenidoWeb/', null=True, blank=True)

    def __str__(self):
        return f"{self.nombre}"

class InformacionWeb(models.Model):
    nombre = models.CharField(max_length=50, blank=True, null=True)
    contenido = models.TextField(null=True, blank=True)
    imagen = models.ImageField(storage=S3Boto3Storage(), upload_to='contenidoWeb/', null=True, blank=True)

class PuntosClub(models.Model):
    activo = models.BooleanField(default=False)

class Diseños(models.Model):
    nombre = models.CharField(max_length=50)
    activo = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre}- {self.activo}"