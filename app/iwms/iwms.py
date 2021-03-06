from app.core.core import CoreModule
from app.auth.models import User,Role
from .models import *
from app.core.models import CoreLog

class IwmsModule(CoreModule):
    module_name = 'iwms'
    module_icon = 'fa-cubes'
    module_link = 'bp_iwms.dashboard'
    module_short_description = 'Warehouse Management'
    module_long_description = "Warehouse Management system"
    models = [User,Group,Department,Warehouse,  \
        Zone,BinLocation,Category,UnitOfMeasure,StockItem,StockItemType,StockReceipt,Putaway,PurchaseOrder,\
            Term,Supplier,CoreLog,Source,ShipVia,Client,InventoryItem,SalesOrder,Picking,StockTransfer]
    no_admin_models = [Role]
    version = '1.0'