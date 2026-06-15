from . import bookings
from . import services
from . import admin

# Create placeholder modules for auth and payments if needed
try:
    from . import auth
except ImportError:
    pass

try:
    from . import payments
except ImportError:
    pass