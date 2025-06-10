import os
import sys
import traceback
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')

try:
    application = get_wsgi_application()
except Exception:
    print("Erro ao iniciar WSGI:")
    traceback.print_exc()
    sys.exit(1)
