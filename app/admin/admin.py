""" THIS IS FOR ADMIN MODELS """

from app.auth.models import User,Role
from app.core.core import CoreModule

class AdminModule(CoreModule):
    module_name = 'admin'
    module_icon = 'fa-cogs'
    module_link = 'bp_admin.apps'
    module_short_description = 'Application'
    module_long_description = "Administrator Dashboard and pages"
    models = []
    no_admin_models = []
    version = '1.0'