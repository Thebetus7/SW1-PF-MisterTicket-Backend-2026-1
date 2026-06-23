from django.http import HttpResponse
from django.views import View


class LibelulaRetornoView(View):
    """
    GET /api/pagos/libelula/retorno/

    Endpoint publico al que Libelula redirige al usuario dentro del WebView
    una vez que el pago finaliza (exitoso o cancelado).

    Libelula solo acepta URLs https://, por lo que no podemos usar
    directamente el deep-link miapp://pago-completado.  Esta pagina actua
    como puente: recibe la redireccion de Libelula y, via JavaScript,
    redirige al deep-link para que el NavigationDelegate del WebView lo
    intercepte y cierre la pantalla de pago.

    Query params que Libelula puede incluir (depende de su implementacion):
        ?estado=pagado | rechazado | cancelado
        ?identificador=<uuid>
    """

    def get(self, request, *args, **kwargs):
        # Reenviar todos los query params al deep-link para que Flutter
        # los pueda leer si los necesita en el futuro.
        qs = request.META.get('QUERY_STRING', '')
        deep_link = f'miapp://pago-completado{"?" + qs if qs else ""}'

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Redirigiendo...</title>
  <style>
    body {{
      background: #0F0F1A;
      color: #fff;
      font-family: sans-serif;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
      margin: 0;
      flex-direction: column;
      gap: 16px;
    }}
    p {{ color: #ffffff99; font-size: 14px; }}
  </style>
</head>
<body>
  <p>Volviendo a la aplicacion...</p>
  <script>
    // Redirigir al deep-link para que el WebView lo intercepte
    window.location.href = "{deep_link}";
  </script>
</body>
</html>"""
        return HttpResponse(html, content_type='text/html')
