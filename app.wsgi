import sys
import logging
sys.path.insert(0, '/var/www/asgs')
sys.path.insert(0, '/var/www/asgs/api')
logging.basicConfig(stream=sys.stderr)

from app import app as application
