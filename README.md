# Sollu Store Backend

**Backend API para Sollu Store — Gestión completa de e-commerce con Django**

Este backend maneja toda la lógica y administración central de la tienda online Sollu Store. Gestiona usuarios, roles, productos, categorías, descuentos, ventas, carrito de compras, sesiones, autenticación segura, envío de correos, integraciones con pasarelas de pago, almacenamiento en S3 y más.

---

## 🚀 Funcionalidades Principales

- **Gestión de Usuarios y Roles**  
  Registro, autenticación con JWT, gestión de perfiles, roles y permisos.  
  Soporte para inicio de sesión social con Google.  
  Recuperación de contraseña vía código de verificación.

- **Gestión de Productos**  
  CRUD completo de productos, categorías, marcas y reseñas.  
  Aplicación y gestión de descuentos.

- **Gestión de Ventas y Compras**  
  Creación y administración de ventas, estados de venta y carritos.  
  Integración con Mercado Pago y PayPal para procesamiento seguro de pagos.  
  Validación y gestión de cupones de descuento.  
  Envío automático de comprobantes en PDF por correo.

- **Configuración y Personalización**  
  Gestión de configuraciones del sitio como temas, colores, fuentes, contenidos web, diseños, puntos de club y más.  
  Soporte para barrios y envíos configurables.

- **Integración con AWS S3**  
  Almacenamiento y gestión de imágenes y archivos en Amazon S3 para escalabilidad y performance.

- **Base de Datos PostgreSQL**  
  Almacenamiento robusto y eficiente de toda la información estructurada.

- **Manejo de Sesiones y Seguridad**  
  Uso de tokens JWT para autenticación y autorización.  
  Protección contra ataques de fuerza bruta con limitación de tasa (`django-ratelimit`).

- **APIs RESTful Documentadas**  
  Endpoints REST organizados en ViewSets para productos, usuarios, ventas, configuraciones, etc.  
  Documentación automática con `drf-yasg` (Swagger).

---

## 🛠 Tecnologías y Librerías Clave

- **Framework:** Django 5.1 con Django REST Framework  
- **Autenticación:** djangorestframework-simplejwt, inicio con Google OAuth  
- **Base de datos:** PostgreSQL  
- **Almacenamiento:** django-storages con Amazon S3  
- **Pasarelas de Pago:** Mercado Pago, PayPal SDK  
- **Envío de correos:** SMTP seguro, generación de PDFs con ReportLab  
- **Limitación de peticiones:** django-ratelimit  
- **Documentación API:** drf-yasg (Swagger)  
- **Otros:** boto3, python-decouple, qrcode, stripe, cryptography

---

## 📦 Instalación y Configuración

1. Clona el repositorio:

```bash
git clone https://github.com/alejandro-samuel-mercado/sollu-store-Backend.git
cd sollu-store-Backend
```

2. Crea y activa un entorno virtual (opcional pero recomendado):

```bash
python -m venv env
source env/bin/activate  # Linux/macOS
env\Scripts\activate     # Windows
```

3. Instala las dependencias:
```bash
pip install -r requirements.txt

```

4. Configura las variables de entorno (crear .env o usar python-decouple) con los datos necesarios:

- **Configuración de base de datos PostgreSQL

- **Credenciales AWS S3

- **Configuración de SMTP para envío de correos

- **Claves y credenciales para Mercado Pago y PayPal

- **Otras vlaves y ajustes de Django

5. Aplica migraciones:
 ```bash
python manage.py migrate
```

6.Carga datos iniciales si aplica:
```bash
python manage.py loaddata initial_data.json
```
Ejecuta el servidor:
```bash
python manage.py runserver
```
📚 Endpoints Principales
- **Configuración y ajustes:
/envio/, /barrios/, /reviews/, /cupones/, /componentes/, /colores/, /temas/, /contenidosWeb/, /informacionWeb/, /fuentes/, /fuentes-aplicar/, /diseños/, /puntos-club/

- **Productos:
/productos/, /categorias/, /descuentos/, /marcas/, /reviewsProducts/

- **Usuarios:
/vendedores/, /perfilesUsuarios/, /historial-puntos/, /roles/

- **Registro: /registro/

- **Autenticación JWT: /auth/token/, /auth/token/refresh/

- **Login social: /auth/google/

 - **Restablecimiento de contraseña:
/auth/password-reset/request/
/auth/password-reset/verify/
/auth/password-reset/confirm/

- **Ventas y carrito:
/ventas/, /estados/, /carrito/
Creación de venta: /crear-venta/
Creación de preferencia de pago: /pago/
Webhook para pagos Mercado Pago: /webhook/
Verificación de pago: /verificar-pago/
Envío de comprobantes PDF: /enviar-pdf/

- **Otros:
Validación de cupones: /validar-cupon/
Datos home: /home-data/
Gestión usuarios: /usuarios/, /usuarios/<int:user_id>/
Envío de email contacto: /enviar-mail/


💡 Contribuciones
Si deseas contribuir, sigue estos pasos:

- **Haz un fork del repositorio.

- **Crea una rama para tu funcionalidad:
git checkout -b feature/nueva-funcionalidad

- **Realiza tus cambios y haz commit con mensaje claro.
- 
- **Sube tus cambios a tu fork:
git push origin feature/nueva-funcionalidad

- **Abre un Pull Request describiendo tus cambios.

📄 Licencia
Este proyecto está bajo la Licencia MIT. Consulta el archivo LICENSE para más detalles.
