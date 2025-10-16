import os
import sys
import traceback
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')

try:
    application = get_wsgi_application()
except Exception:
    print(">>> ERRO AO INICIAR O WSGI <<<", flush=True)
    traceback.print_exc(file=sys.stdout)
    sys.exit(1)
