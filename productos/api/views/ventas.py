from productos.api.common import *
from productos.models.venta import Venta, Carrito, CarritoProducto, EstadosVenta
from productos.models.producto import Producto, Atributo, Marca,ProductoAtributo
from productos.models.usuario import SuperUsuario
from productos.api.serializers.ventas import (
    VentaSerializer, CarritoSerializer, CarritoProductoSerializer, EstadosVentaSerializer
)
from django.core.files import File

class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all().prefetch_related('detalles')
    serializer_class = VentaSerializer

    def get_permissions(self):
        if self.request.user.is_staff:
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            self.permission_classes = [IsAuthenticated, SoloLecturaUsuario]
        return super().get_permissions()

    def get_queryset(self):
        if self.request.user.is_staff:
            return Venta.objects.all().prefetch_related('detalles')
        else:
            return Venta.objects.filter(comprador=self.request.user).prefetch_related('detalles')

    def partial_update(self, request, *args, **kwargs):
        logger.debug("Datos recibidos en partial_update:", request.data)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            logger.error("Error en serializer.is_valid():", str(e))
            raise
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=True, methods=['GET'], url_path='descargar-comprobante')
    def descargar_comprobante(self, request, pk=None):
        try:
            venta = self.get_object()
            if not venta.comprobante_pdf:
                return Response({"error": "No hay comprobante disponible para esta venta"}, 
                                status=status.HTTP_404_NOT_FOUND)
            
            if not request.user.is_staff and venta.comprador != request.user:
                return Response({"error": "No tienes permiso para acceder a este comprobante"},
                                status=status.HTTP_403_FORBIDDEN)

            pdf_url = venta.comprobante_pdf.url
            return Response({"pdf_url": pdf_url}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error al descargar comprobante: {str(e)}")
            return Response({"error": "Ocurrió un error al procesar la solicitud"}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'], url_path='mis-compras')
    def mis_compras(self, request):
        try:
            usuario = request.user
            ventas = Venta.objects.filter(comprador=usuario)
            serializer = VentaSerializer(ventas, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error en mis_compras: {str(e)}")
            return Response({"error": "Ocurrió un error al procesar la solicitud"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'], url_path='mis-ventas')
    def mis_ventas(self, request):
        try:
            usuario = request.user
            ventas = Venta.objects.filter(vendedor__usuario=usuario)
            serializer = VentaSerializer(ventas, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error en mis_ventas: {str(e)}")
            return Response({"error": "Ocurrió un error al procesar la solicitud"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'], url_path='ventas-por-vendedor')
    def ventas_por_vendedor(self, request):
        try:
            ventas_agrupadas = Venta.objects.values('vendedor__id', 'vendedor__nombre', 'vendedor__usuario__username', 'vendedor__dni')\
                .annotate(
                    numero_ventas=Count('id'),
                    total_recaudado=Sum('precio_total')
                ).order_by('vendedor__id')

            resultado = [
                {
                    'vendedor_id': venta['vendedor__id'],
                    'nombre': venta['vendedor__nombre'],
                    'username': venta['vendedor__usuario__username'],
                    'dni': venta['vendedor__dni'],
                    'numero_ventas': venta['numero_ventas'],
                    'total_recaudado': float(venta['total_recaudado']) if venta['total_recaudado'] else 0.0
                }
                for venta in ventas_agrupadas
            ]
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error en ventas_por_vendedor: {str(e)}")
            return Response({"error": "Ocurrió un error al procesar la solicitud"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EstadosVentaViewSet(viewsets.ModelViewSet):
    queryset = EstadosVenta.objects.all()
    serializer_class = EstadosVentaSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()

class CarritoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Carrito.objects.all()

    def list(self, request):
        usuario = request.user
        logger.info(f"Usuario autenticado: {usuario}, ID: {usuario.id}")
        carrito, created = Carrito.objects.get_or_create(usuario=usuario)
        if created:
            logger.info(f"Carrito creado para el usuario: {carrito.id}")
        else:
            logger.info(f"Carrito encontrado: {carrito.id}")
        serializer = CarritoSerializer(carrito)
        logger.debug("Datos serializados:", serializer.data)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='agregar_producto')
    def agregar_producto(self, request):
        carrito, created = Carrito.objects.get_or_create(usuario=request.user)
        serializer = CarritoProductoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(carrito=carrito)
        return Response(CarritoSerializer(carrito).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['delete'], url_path='eliminar_producto')
    def eliminar_producto(self, request):
        carrito = Carrito.objects.get(usuario=request.user)
        producto_atributo_id = request.data.get('producto_atributo_id')
        if not producto_atributo_id:
            return Response({'detail': 'producto_atributo_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            producto = carrito.productos.get(producto_atributo_id=producto_atributo_id)
            producto.delete()
            return Response(CarritoSerializer(carrito).data)
        except CarritoProducto.DoesNotExist:
            return Response({'detail': 'Producto no encontrado en el carrito'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_venta(request):
    logger.info("Datos recibidos: %s", request.data)
    data = request.data.copy()

    if 'productos' in data and 'detalles' not in data:
        data['detalles'] = [
            {
                'producto_id': p['producto'],
                'combinacion': p.get('combinacion', []),
                'cantidad': p['cantidad'],
                'precio_unitario': p['precio_unitario'],
                'subtotal': float(p['precio_unitario']) * p['cantidad']
            } for p in data.pop('productos')
        ]

    serializer = VentaSerializer(data=data, context={'request': request})
    if serializer.is_valid():
        try:
            with transaction.atomic():
                detalles_data = serializer.validated_data['detalles']
                productos_ids = [d['producto'].id for d in detalles_data]
                productos = Producto.objects.select_for_update().filter(id__in=productos_ids)
                productos_dict = {p.id: p for p in productos}

                for detalle in detalles_data:
                    producto = productos_dict.get(detalle['producto'].id)
                    if not producto:
                        logger.error("Producto con ID %s no encontrada.", detalle['producto'].id)
                        return Response({'error': f'Producto con ID {detalle["producto"].id} no encontrada.'}, 
                                        status=status.HTTP_400_BAD_REQUEST)
                    combinacion_key = ",".join(f"{item['tipo']}:{item['valor']}" for item in detalle['combinacion']) \
                        if detalle['combinacion'] else "default"
                    if producto.tiene_variantes and combinacion_key not in producto.combinaciones:
                        logger.error("Combinación %s no encontrada.", combinacion_key)
                        return Response({'error': f'Combinación {combinacion_key} no encontrada.'}, 
                                        status=status.HTTP_400_BAD_REQUEST)
                    stock = producto.combinaciones.get(combinacion_key, {}).get('stock', 0)
                    if stock < detalle['cantidad']:
                        logger.error("Stock insuficiente para %s.", producto.nombre)
                        return Response({'error': f'Stock insuficiente para {producto.nombre}.'}, 
                                        status=status.HTTP_400_BAD_REQUEST)

                venta = serializer.save()
                logger.info("Venta creada con éxito: %s", venta.id)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.exception("Error al crear la venta: %s", str(e))
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    logger.error("Errores de validación: %s", serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enviar_pdf(request):
    try:
        usuario = request.user
        if not usuario.is_authenticated:
            return JsonResponse({"error": "Usuario no autenticado"}, status=401)

        data = request.data
        venta_id = data.get('venta_id')
        datos_compra = data.get('datos_compra')
        total_puntos = data.get('total_puntos', 0)

        if not venta_id or not datos_compra:
            return JsonResponse({"error": "Se requieren venta_id y datos_compra"}, status=400)

        venta = Venta.objects.get(id=venta_id)
        
        if not usuario.is_staff and venta.comprador != usuario:
            return JsonResponse({"error": "No tienes permiso para esta venta"}, status=403)

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=8*mm,
            leftMargin=8*mm,
            topMargin=8*mm,
            bottomMargin=8*mm
        )
        styles = getSampleStyleSheet()
        elements = []

        page_width = doc.width 
        y_position = 0

        elements.append(Spacer(1, y_position))  
        styles["Title"].fontSize = 12
        styles["Title"].textColor = colors.black
        styles["Title"].fontName = "Helvetica-Bold"
        elements.append(Paragraph("Factura Fiscal", styles["Title"]))
        
        styles["Heading1"].fontSize = 20
        styles["Heading1"].alignment = 2  
        elements.append(Paragraph(
            datos_compra.get('datosEmpresa', {}).get('nombre', '').get('contenido',''),
            styles["Heading1"]
        ))
        
        styles["Normal"].fontSize = 10
        styles["Normal"].alignment = 2  
        elements.append(Paragraph(
            f"Dirección: {datos_compra.get('datosEmpresa', {}).get('direccion', 'N/A').get('contenido','')}, "
            f"{datos_compra.get('datosEmpresa', {}).get('ciudad', 'N/A').get('contenido','')}, "
            f"{datos_compra.get('datosEmpresa', {}).get('pais', 'N/A').get('contenido','')}",
            styles["Normal"]
        ))
        elements.append(Paragraph(
            f"Tel: {datos_compra.get('datosEmpresa', {}).get('telefono', 'N/A').get('contenido','')} | "
            f"Email: {datos_compra.get('datosEmpresa', {}).get('email', 'N/A').get('contenido','')}",
            styles["Normal"]
        ))
        elements.append(Spacer(1, 35))  

        styles["Heading3"].fontSize = 12
        styles["Heading3"].fontName = "Helvetica-Bold"
        elements.append(Paragraph(f"Factura N°: {str(venta_id).zfill(8)}", styles["Heading3"]))
        
        styles["Normal"].fontSize = 12
        styles["Normal"].alignment = 2  
        elements.append(Paragraph(
            f"Fecha de Emisión: {timezone.now().strftime('%d/%m/%Y')}",
            styles["Normal"]
        ))
        elements.append(Spacer(1, 10))

        styles["Heading4"].fontSize = 12
        styles["Heading4"].fontName = "Helvetica-Bold"
        elements.append(Paragraph("Cliente:", styles["Heading4"]))
        elements.append(Spacer(1, 5))
        
        styles["Normal"].fontSize = 12
        styles["Normal"].alignment = 0 
        elements.append(Paragraph(f"Nombre: {datos_compra.get('nombre', 'Desconocido')}", styles["Normal"]))
        elements.append(Paragraph(f"Teléfono: {datos_compra.get('telefono', 'No disponible')}", styles["Normal"]))
        elements.append(Paragraph(f"Correo: {datos_compra.get('correo', 'No disponible')}", styles["Normal"]))
        elements.append(Paragraph(f"Dirección: {datos_compra.get('domicilio', 'No disponible')}", styles["Normal"]))
        elements.append(Paragraph(f"Ciudad: {datos_compra.get('cityComprador', 'N/A')}", styles["Normal"]))
        elements.append(Paragraph(f"País/Estado: {datos_compra.get('paisComprador', 'N/A')}", styles["Normal"]))
        elements.append(Paragraph(f"ID Fiscal: {datos_compra.get('idFiscal', usuario.id or 'No proporcionado')}", styles["Normal"]))
        elements.append(Spacer(1, 35))

        elements.append(Paragraph("Detalles de Entrega:", styles["Heading4"]))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(f"Método: {datos_compra.get('finalEnvio', 'No disponible')}", styles["Normal"]))
        elements.append(Paragraph(
            f"Fecha de Venta: {datos_compra.get('fecha_venta', '').split('T')[0] if datos_compra.get('fecha_venta') else 'No disponible'}",
            styles["Normal"]
        ))
        elements.append(Paragraph(
            f"Fecha de Entrega: {datos_compra.get('fecha_entrega', '').split('T')[0] if datos_compra.get('fecha_entrega') else 'No disponible'}",
            styles["Normal"]
        ))
        elements.append(Paragraph(f"Horario: {datos_compra.get('horario_entrega', 'No disponible')}", styles["Normal"]))
        elements.append(Spacer(1, 20))

        elements.append(Table(
            [['']],
            colWidths=[page_width],
            rowHeights=[1],
            style=TableStyle([('LINEBELOW', (0, 0), (-1, -1), 1, colors.black)])
        ))
        elements.append(Spacer(1, 10))

        styles["Heading2"].fontSize = 14
        styles["Heading2"].fontName = "Helvetica-Bold"
        elements.append(Paragraph("Detalles de la Compra", styles["Heading2"]))
        elements.append(Spacer(1, 5))

        productos_data = [["#", "Descripción", "Precio Unitario", "Cantidad", "Subtotal"]]
        for index, item in enumerate(datos_compra.get('productos', []), 1):
            precio_unitario = float(item.get('precio_unitario', 0))
            cantidad = item.get('cantidad', 1)
            subtotal_item = precio_unitario * cantidad
            # Obtener atributos de la variante
            try:
                variante = Variante.objects.get(id=item.get('producto'))
                atributos = [
                    {'nombre': attr.nombre, 'valor': attr.valor}
                    for attr in variante.atributos.all()
                ]
                atributos_str = ", ".join([f"{attr['nombre']}: {attr['valor']}" for attr in atributos]) if atributos else "N/A"
                nombre_producto = f"{variante.producto.marca.nombre} {variante.producto.nombre}"
            except Variante.DoesNotExist:
                atributos_str = "N/A"
                nombre_producto = item.get('nombre', 'Desconocido')

            productos_data.append([
                str(index),
                f"{nombre_producto} ({atributos_str})",
                f"${precio_unitario:.2f}",
                str(cantidad),
                f"${subtotal_item:.2f}"
            ])

        tabla = Table(productos_data, colWidths=[10*mm, 90*mm, 30*mm, 20*mm, 30*mm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(50/255, 50/255, 50/255)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(tabla)

        elements.append(Spacer(1, 10))
        tasa_impuesto = float(datos_compra.get('impuesto', 0)) / 100
        precio_final_sin_impuesto = float(datos_compra.get('precioFinalSinImpuesto', datos_compra.get('precioFinal', 0)))
        precio_envio = float(datos_compra.get('precioEnvio', 0))
        impuesto_valor = precio_final_sin_impuesto * tasa_impuesto
        total_con_impuestos = float(datos_compra.get('precioFinal', precio_final_sin_impuesto + precio_envio))

        styles["Normal"].fontSize = 12
        styles["Normal"].alignment = 2  
        elements.append(Paragraph(f"Subtotal: ${precio_final_sin_impuesto:.2f}", styles["Normal"]))
        elements.append(Paragraph(f"Envío: ${precio_envio:.2f}", styles["Normal"]))
        elements.append(Paragraph(f"Impuesto ({tasa_impuesto * 100:.1f}%): ${impuesto_valor:.2f}", styles["Normal"]))
        styles["Heading2"].fontSize = 12
        styles["Heading2"].alignment = 2
        elements.append(Paragraph(f"Total: ${total_con_impuestos:.2f}", styles["Normal"]))
        moneda = datos_compra.get('datosEmpresa', {}).get('moneda_local', '').get('contenido','')
        elements.append(Paragraph(f"Moneda: {moneda}", styles["Normal"]))
        elements.append(Spacer(1, 50))

        styles["Normal"].alignment = 0  
        elements.append(Paragraph(f"Puntos acumulados: {total_puntos}", styles["Normal"]))
        elements.append(Spacer(1, 10))

        styles["Normal"].fontSize = 8
        styles["Normal"].textColor = colors.Color(100/255, 100/255, 100/255)
        legal_text = (
            "Este documento es un comprobante fiscal válido. Conservar para fines fiscales.<br/>"
            f"Emitido conforme a las leyes fiscales aplicables en {datos_compra.get('datosEmpresa', {}).get('pais', 'N/A')}.<br/>"
            "Para reclamos, contactar a info@empresa.com dentro de los 30 días posteriores a la emisión."
        )
        elements.append(Paragraph(legal_text, styles["Normal"]))

        doc.build(elements)

        pdf_name = f"Factura_{str(venta_id).zfill(8)}.pdf"
        buffer.seek(0)
        venta.comprobante_pdf.save(pdf_name, File(buffer), save=True)

        email = EmailMessage(
            subject=f"Factura #{venta_id}",
            body=f"Hola {datos_compra.get('nombre', usuario.username)},\n\nAdjuntamos el comprobante de tu compra (Factura #{venta_id}).\n\nGracias por tu compra!",
            from_email=os.getenv('EMAIL_HOST'),
            to=[datos_compra.get('correo', usuario.email)],
        )
        email.attach(f"Factura_{str(venta_id).zfill(8)}.pdf", buffer.getvalue(), "application/pdf")
        email.send()

        pdf_url = request.build_absolute_uri(venta.comprobante_pdf.url)
        
        logger.info(f"PDF enviado con éxito para la venta #{venta_id} a {datos_compra.get('correo', usuario.email)}")
        return JsonResponse({"pdf_url": pdf_url}, status=200)

    except Venta.DoesNotExist:
        logger.error(f"Venta con ID {venta_id} no encontrada")
        return JsonResponse({"error": "Venta no encontrada"}, status=404)
    except ValueError as ve:
        logger.error(f"Error de conversión de valores: {str(ve)}")
        return JsonResponse({"error": "Datos numéricos inválidos enviados desde el frontend"}, status=400)
    except Exception as e:
        logger.error(f"Error al enviar PDF: {str(e)}")
        return JsonResponse({"error": "Ocurrió un error al procesar la solicitud"}, status=500)

@csrf_exempt
def crear_preferencia(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email_usuario = data.get("email", "")
            items = data.get("items", [])
            total = data.get("total", "")
            country = data.get("country", "AR")

            if country in ["AR", "BR", "MX", "CO"]:
                return crear_preferencia_mercadopago(email_usuario, items, total, country)
            else:
                return crear_preferencia_paypal(email_usuario, items, total, country)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Datos JSON inválidos"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Método no permitido"}, status=405)

def crear_preferencia_mercadopago(email, items, total, country):
    preference_data = {
        "items": [
            {
                "title": "Productos en Tienda Sollu-store",
                "quantity": 1,
                "unit_price": float(total),
                "currency_id": "ARS" if country == "AR" else "BRL" if country == "BR" else "MXN"
            },
            {
                "title": "Productos en Tienda Sollu-store",
                "quantity": 1,
                "unit_price": 0,
                "currency_id": "ARS" if country == "AR" else "BRL" if country == "BR" else "MXN"
            }
        ],
        "payer": {"email": email},
        "back_urls": {
            "success": f'{os.getenv("URL_FRONTEND")}/pago-exitoso',
            "failure": f'{os.getenv("URL_FRONTEND")}/pago-fallido',
            "pending": f'{os.getenv("URL_FRONTEND")}/pago-pendiente'
        },
        "auto_return": "approved"
    }
    preference_response = sdk.preference().create(preference_data)
    if "response" in preference_response and "init_point" in preference_response["response"]:
        return JsonResponse({"init_point": preference_response["response"]["init_point"]})
    else:
        return JsonResponse({"error": "Error al generar la preferencia en Mercado Pago"}, status=500)

def crear_preferencia_paypal(email, items, total, country):
    try:
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "transactions": [{
                "amount": {
                    "total": str(total),
                    "currency": "USD"
                },
                "description": ", ".join(items)
            }],
            "redirect_urls": {
                "return_url": f'{os.getenv("URL_FRONTEND")}/pago-exitoso',
                "cancel_url": f'{os.getenv("URL_FRONTEND")}/pago-fallido'
            }
        })
        if payment.create():
            for link in payment.links:
                if link.method == "REDIRECT":
                    return JsonResponse({"payment_url": link.href})
        else:
            return JsonResponse({"error": payment.error}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def webhook_mp(request):
    if request.method == "POST":
        data = json.loads(request.body)
        payment_id = data.get("data", {}).get("id", None)
        if payment_id:
            payment_info = sdk.payment().get(payment_id)
            if "response" in payment_info:
                payment_status = payment_info["response"]["status"]
                status_detail = payment_info["response"]["status_detail"]
                email_cliente = payment_info["response"]["payer"]["email"]
                monto = payment_info["response"]["transaction_amount"]
                logger.info(f"Pago recibido: ID {payment_id}, Status {payment_status}, Monto {monto}")
        return JsonResponse({"status": "received"}, status=200)
    return JsonResponse({"error": "Método no permitido"}, status=405)

def verificar_pago(request):
    payment_id = request.GET.get('payment_id')
    preference_id = request.GET.get('preference_id')
    payment_info = sdk.payment().get(payment_id)
    if payment_info["status"] == "approved":
        return JsonResponse({"status": "success"})
    else:
        return JsonResponse({"status": "failure"})



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enviar_pdf(request):
    try:
        usuario = request.user
        if not usuario.is_authenticated:
            return JsonResponse({"error": "Usuario no autenticado"}, status=401)

        data = request.data
        venta_id = data.get('venta_id')
        datos_compra = data.get('datos_compra')
        total_puntos = data.get('total_puntos', 0)

        if not venta_id or not datos_compra:
            return JsonResponse({"error": "Se requieren venta_id y datos_compra"}, status=400)

        venta = Venta.objects.get(id=venta_id)
        
        if not usuario.is_staff and venta.comprador != usuario:
            return JsonResponse({"error": "No tienes permiso para esta venta"}, status=403)

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=8*mm,
            leftMargin=8*mm,
            topMargin=8*mm,
            bottomMargin=8*mm
        )
        styles = getSampleStyleSheet()
        elements = []

        page_width = doc.width 
        y_position = 0

        elements.append(Spacer(1, y_position))  
        styles["Title"].fontSize = 12
        styles["Title"].textColor = colors.black
        styles["Title"].fontName = "Helvetica-Bold"
        elements.append(Paragraph("Factura Fiscal", styles["Title"]))
        
        styles["Heading1"].fontSize = 20
        styles["Heading1"].alignment = 2  
        elements.append(Paragraph(
            datos_compra.get('datosEmpresa', {}).get('nombre', '').get('contenido',''),
            styles["Heading1"]
        ))
        
        styles["Normal"].fontSize = 10
        styles["Normal"].alignment = 2  
        elements.append(Paragraph(
            f"Dirección: {datos_compra.get('datosEmpresa', {}).get('direccion', 'N/A').get('contenido','')}, "
            f"{datos_compra.get('datosEmpresa', {}).get('ciudad', 'N/A').get('contenido','')}, "
            f"{datos_compra.get('datosEmpresa', {}).get('pais', 'N/A').get('contenido','')}",
            styles["Normal"]
        ))
        elements.append(Paragraph(
            f"Tel: {datos_compra.get('datosEmpresa', {}).get('telefono', 'N/A').get('contenido','')} | "
            f"Email: {datos_compra.get('datosEmpresa', {}).get('email', 'N/A').get('contenido','')}",
            styles["Normal"]
        ))
        elements.append(Spacer(1, 35))  

        styles["Heading3"].fontSize = 12
        styles["Heading3"].fontName = "Helvetica-Bold"
        elements.append(Paragraph(f"Factura N°: {str(venta_id).zfill(8)}", styles["Heading3"]))
        
        styles["Normal"].fontSize = 12
        styles["Normal"].alignment = 2  
        elements.append(Paragraph(
            f"Fecha de Emisión: {timezone.now().strftime('%d/%m/%Y')}",
            styles["Normal"]
        ))
        elements.append(Spacer(1, 10))

        styles["Heading4"].fontSize = 12
        styles["Heading4"].fontName = "Helvetica-Bold"
        elements.append(Paragraph("Cliente:", styles["Heading4"]))
        elements.append(Spacer(1, 5))
        
        styles["Normal"].fontSize = 12
        styles["Normal"].alignment = 0 
        elements.append(Paragraph(f"Nombre: {datos_compra.get('nombre', 'Desconocido')}", styles["Normal"]))
        elements.append(Paragraph(f"Teléfono: {datos_compra.get('telefono', 'No disponible')}", styles["Normal"]))
        elements.append(Paragraph(f"Correo: {datos_compra.get('correo', 'No disponible')}", styles["Normal"]))
        elements.append(Paragraph(f"Dirección: {datos_compra.get('domicilio', 'No disponible')}", styles["Normal"]))
        elements.append(Paragraph(f"Ciudad: {datos_compra.get('cityComprador', 'N/A')}", styles["Normal"]))
        elements.append(Paragraph(f"País/Estado: {datos_compra.get('paisComprador', 'N/A')}", styles["Normal"]))
        elements.append(Paragraph(f"ID Fiscal: {datos_compra.get('idFiscal', usuario.id or 'No proporcionado')}", styles["Normal"]))
        elements.append(Spacer(1, 35))

        elements.append(Paragraph("Detalles de Entrega:", styles["Heading4"]))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(f"Método: {datos_compra.get('finalEnvio', 'No disponible')}", styles["Normal"]))
        elements.append(Paragraph(
            f"Fecha de Venta: {datos_compra.get('fecha_venta', '').split('T')[0] if datos_compra.get('fecha_venta') else 'No disponible'}",
            styles["Normal"]
        ))
        elements.append(Paragraph(
            f"Fecha de Entrega: {datos_compra.get('fecha_entrega', '').split('T')[0] if datos_compra.get('fecha_entrega') else 'No disponible'}",
            styles["Normal"]
        ))
        elements.append(Paragraph(f"Horario: {datos_compra.get('horario_entrega', 'No disponible')}", styles["Normal"]))
        elements.append(Spacer(1, 20))

        elements.append(Table(
            [['']],
            colWidths=[page_width],
            rowHeights=[1],
            style=TableStyle([('LINEBELOW', (0, 0), (-1, -1), 1, colors.black)])
        ))
        elements.append(Spacer(1, 10))

        styles["Heading2"].fontSize = 14
        styles["Heading2"].fontName = "Helvetica-Bold"
        elements.append(Paragraph("Detalles de la Compra", styles["Heading2"]))
        elements.append(Spacer(1, 5))

        productos_data = [["#", "Descripción", "Precio Unitario", "Cantidad", "Subtotal"]]
        for index, item in enumerate(datos_compra.get('productos', []), 1):
            precio_unitario = float(item.get('precio_unitario', 0))
            cantidad = item.get('cantidad', 1)
            subtotal_item = precio_unitario * cantidad
            atributos = item.get('atributos', [])
            atributos_str = ", ".join([f"{attr['nombre']}: {attr['valor']}" for attr in atributos]) if atributos else "N/A"
            productos_data.append([
                str(index),
                f"{item.get('nombre', 'Desconocido')} ({atributos_str})",
                f"${precio_unitario:.2f}",
                str(cantidad),
                f"${subtotal_item:.2f}"
            ])

        tabla = Table(productos_data, colWidths=[10*mm, 90*mm, 30*mm, 20*mm, 30*mm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(50/255, 50/255, 50/255)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(tabla)

        elements.append(Spacer(1, 10))
        tasa_impuesto = float(datos_compra.get('impuesto', 0)) / 100
        precio_final_sin_impuesto = float(datos_compra.get('precioFinalSinImpuesto', datos_compra.get('precioFinal', 0)))
        precio_envio = float(datos_compra.get('precioEnvio', 0))
        impuesto_valor = precio_final_sin_impuesto * tasa_impuesto
        total_con_impuestos = float(datos_compra.get('precioFinal', precio_final_sin_impuesto + precio_envio))

        styles["Normal"].fontSize = 12
        styles["Normal"].alignment = 2  
        elements.append(Paragraph(f"Subtotal: ${precio_final_sin_impuesto:.2f}", styles["Normal"]))
        elements.append(Paragraph(f"Envío: ${precio_envio:.2f}", styles["Normal"]))
        elements.append(Paragraph(f"Impuesto ({tasa_impuesto * 100:.1f}%): ${impuesto_valor:.2f}", styles["Normal"]))
        styles["Heading2"].fontSize = 12
        styles["Heading2"].alignment = 2
        elements.append(Paragraph(f"Total: ${total_con_impuestos:.2f}", styles["Normal"]))
        moneda = datos_compra.get('datosEmpresa', {}).get('moneda_local', '').get('contenido','')
        elements.append(Paragraph(f"Moneda: {moneda}", styles["Normal"]))
        elements.append(Spacer(1, 50))

        styles["Normal"].alignment = 0  
        elements.append(Paragraph(f"Puntos acumulados: {total_puntos}", styles["Normal"]))
        elements.append(Spacer(1, 10))

        styles["Normal"].fontSize = 8
        styles["Normal"].textColor = colors.Color(100/255, 100/255, 100/255)
        legal_text = (
            "Este documento es un comprobante fiscal válido. Conservar para fines fiscales.<br/>"
            f"Emitido conforme a las leyes fiscales aplicables en {datos_compra.get('datosEmpresa', {}).get('pais', 'N/A')}.<br/>"
            "Para reclamos, contactar a info@empresa.com dentro de los 30 días posteriores a la emisión."
        )
        elements.append(Paragraph(legal_text, styles["Normal"]))

        doc.build(elements)

        pdf_name = f"Factura_{str(venta_id).zfill(8)}.pdf"
        buffer.seek(0)
        venta.comprobante_pdf.save(pdf_name, File(buffer), save=True)

        email = EmailMessage(
            subject=f"Factura #{venta_id}",
            body=f"Hola {datos_compra.get('nombre', usuario.username)},\n\nAdjuntamos el comprobante de tu compra (Factura #{venta_id}).\n\nGracias por tu compra!",
            from_email=os.getenv('EMAIL_HOST'),
            to=[datos_compra.get('correo', usuario.email)],
        )
        email.attach(f"Factura_{str(venta_id).zfill(8)}.pdf", buffer.getvalue(), "application/pdf")
        email.send()

        pdf_url = request.build_absolute_uri(venta.comprobante_pdf.url)
        
        logger.info(f"PDF enviado con éxito para la venta #{venta_id} a {datos_compra.get('correo', usuario.email)}")
        return JsonResponse({"pdf_url": pdf_url}, status=200)

    except Venta.DoesNotExist:
        logger.error(f"Venta con ID {venta_id} no encontrada")
        return JsonResponse({"error": "Venta no encontrada"}, status=404)
    except ValueError as ve:
        logger.error(f"Error de conversión de valores: {str(ve)}")
        return JsonResponse({"error": "Datos numéricos inválidos enviados desde el frontend"}, status=400)
    except Exception as e:
        logger.error(f"Error al enviar PDF: {str(e)}")
        return JsonResponse({"error": "Ocurrió un error al procesar la solicitud"}, status=500)