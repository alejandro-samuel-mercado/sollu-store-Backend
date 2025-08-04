# Configuración de Gunicorn
bind = "unix:/var/www/Proyecto-Tienda_Sol/backend/tienda_ropa.sock" 
workers = 5 
worker_class = "sync"
loglevel = "debug"
errorlog = "/var/www/Proyecto-Tienda_Sol/backend/logs/gunicorn_error.log"
accesslog = "/var/www/Proyecto-Tienda_Sol/backend/logs/gunicorn_access.log"
timeout = 30