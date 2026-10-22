from .admin import *
from .integrations import *
from .user import *

routers = [*admin_routers, *user_routers, *integration_routers]
