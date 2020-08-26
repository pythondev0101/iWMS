""" MODELS """


""" APP IMPORTS  """
from app import db
from app.core.models import Base
from app.admin.models import Admin
"""--------------END--------------"""
import enum
from datetime import datetime


class Group(Base,Admin):
    __tablename__ = 'iwms_group'
    __amname__ = 'group'
    __amicon__ = 'pe-7s-users'
    __amdescription__ = "Groups"
    
    """ COLUMNS """
    name = db.Column(db.String(64),nullable=False)


class Department(Base,Admin):
    __tablename__ =  'iwms_department'
    __amname__ = 'department'
    __amicon__ = 'pe-7s-culture'
    __amdescription__ = "Departments"

    """ COLUMNS """
    name = db.Column(db.String(64),nullable=False)


class TransactionType(Base,Admin):
    __tablename__ = 'iwms_transaction_type'
    __amname__ = 'transaction_type'
    __amdescription__ = "Transaction Types"
    __amicon__ = 'pe-7s-network'

    """ COLUMNS """
    code = db.Column(db.String(64),nullable=False,unique=True)
    description = db.Column(db.String(255),nullable=True)
    prefix = db.Column(db.String(64),nullable=False)
    next_number_series = db.Column(db.Integer,nullable=True)


class Email(Base,Admin):
    __tablename__ = 'iwms_email'
    __amname__ = 'email'
    __amdescription__ = 'Email Address'
    __amicon__ = 'pe-7s-mail'

    """ COLUMNS """
    email = db.Column(db.String(64),nullable=False)
    module_code = db.Column(db.String(64),nullable=False)
    description = db.Column(db.String(255),nullable=True)
    type = db.Column(db.String(64),nullable=False)


class Warehouse(Base,Admin):
    __tablename__ = 'iwms_warehouse'
    __amname__ = 'warehouse'
    __amdescription__ = 'Warehouse'
    __amicon__ = 'pe-7s-map'

    """ COLUMNS """
    code = db.Column(db.String(64),nullable=False,unique=True)
    name = db.Column(db.String(64),nullable=False)
    main_warehouse = db.Column(db.Boolean, nullable=False, default="0")
    bins = db.relationship('BinLocation',backref='warehouse')


class Zone(Base,Admin):
    __tablename__ = 'iwms_zone'
    __amname__ = 'zone'
    __amdescription__ = 'Zone'
    __amicon__ = 'pe-7s-map-2'

    """ COLUMNS """
    code = db.Column(db.String(64),nullable=False,unique=True)
    description = db.Column(db.String(255),nullable=True)

    @property
    def name(self):
        return self.code
        

class BinLocation(Base,Admin):
    __tablename__ = 'iwms_bin_location'
    __amname__ = 'bin_location'
    __amdescription__ = 'Bin Location'
    __amicon__ = 'pe-7s-map-marker'

    """ COLUMNS """
    code = db.Column(db.String(64),nullable=False,unique=True)
    description = db.Column(db.String(255),nullable=True)
    index = db.Column(db.Integer,nullable=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('iwms_warehouse.id',ondelete="SET NULL"),nullable=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('iwms_zone.id',ondelete="SET NULL"),nullable=True)
    zone = db.relationship('Zone',backref='binlocationzone')
    pallet_slot = db.Column(db.Integer,default=None)
    pallet_cs = db.Column(db.Integer,default=None)
    capacity = db.Column(db.Integer,default=None)
    weight_cap = db.Column(db.Integer,default=None)
    cbm_cap = db.Column(db.Integer,default=None)
    x = db.Column(db.Integer,nullable=True,default=0)
    y = db.Column(db.Integer,nullable=True,default=0)


class Category(Base,Admin):
    __tablename__ = 'iwms_category'
    __amname__ = 'category'
    __amdescription__ = 'Category'
    __amicon__ = 'pe-7s-network'

    """ COLUMNS """
    code = db.Column(db.String(64),nullable=False,unique=True)
    description = db.Column(db.String(255),nullable=True)
    
    @property
    def name(self):
        return self.description

class StockItemStatus(enum.Enum):
    active = "Active"
    hold = "Hold"

suppliers = db.Table('iwms_suppliers',
    db.Column('supplier_id', db.Integer, db.ForeignKey('iwms_supplier.id'), primary_key=True),
    db.Column('stock_item_id', db.Integer, db.ForeignKey('iwms_stock_item.id'), primary_key=True)
)


class StockItem(Base,Admin):
    __tablename__ = 'iwms_stock_item'
    __amname__ = 'stock_item'
    __amdescription__ = 'Stock Item'
    __amicon__ = 'pe-7s-download'

    """ COLUMNS """
    number = db.Column(db.String(255),nullable=False)
    status = db.Column(db.Enum(StockItemStatus),default=StockItemStatus.active)
    stock_item_type_id = db.Column(db.Integer,db.ForeignKey('iwms_stock_item_type.id',ondelete="SET NULL"),nullable=True)
    stock_item_type = db.relationship('StockItemType',backref='type_stock_items')
    category_id = db.Column(db.Integer,db.ForeignKey('iwms_category.id',ondelete="SET NULL"),nullable=True)
    category = db.relationship('Category',backref='stockitem_category')
    has_serial = db.Column(db.Boolean,default="0")
    monitor_expiration = db.Column(db.Boolean,default=None)
    brand = db.Column(db.String(255),nullable=True,default="")
    name = db.Column(db.String(255),nullable=True,default="")
    description = db.Column(db.String(255),nullable=True,default="")
    cap_size = db.Column(db.Integer,nullable=True,default=None)
    cap_profile = db.Column(db.Integer,nullable=True,default=None)
    compound = db.Column(db.Integer,nullable=True,default=None)
    suppliers = db.relationship('Supplier', secondary=suppliers, lazy='subquery',backref=db.backref('stock_items', lazy=True))
    #TODO: clients = db.Column(db.String(255),nullable=True,default="")
    packaging = db.Column(db.String(255),nullable=True,default="")
    tax_code_id = db.Column(db.Integer,db.ForeignKey('iwms_tax_code.id',ondelete="SET NULL"),nullable=True)
    tax_code = db.relationship("TaxCode",backref='stock_items')
    reorder_qty = db.Column(db.Integer,nullable=True,default=None)
    description_plu = db.Column(db.String(255),nullable=True,default="")
    barcode = db.Column(db.String(255),nullable=True,default=None,unique=True)
    qty_plu = db.Column(db.Integer,nullable=True,default=None)
    length = db.Column(db.String(255),nullable=True,default="")
    width = db.Column(db.String(255),nullable=True,default="")
    height = db.Column(db.String(255),nullable=True,default="")
    unit_id = db.Column(db.Integer,db.ForeignKey('iwms_unit_of_measure.id',ondelete="SET NULL"),nullable=True)
    unit = db.relationship("UnitOfMeasure",backref='unit_stock_items')
    default_cost = db.Column(db.Numeric(10,2),nullable=True,default=None)
    default_price = db.Column(db.Numeric(10,2),nullable=True,default=None)
    weight = db.Column(db.String(255),nullable=True,default="")
    cbm = db.Column(db.String(255),nullable=True,default="")
    qty_per_pallet = db.Column(db.Integer,nullable=True,default=None)
    shelf_life = db.Column(db.Integer,nullable=True,default=None)
    qa_lead_time = db.Column(db.Integer,nullable=True,default=None)
    uom_line = db.relationship('StockItemUomLine', cascade='all,delete', backref="stock_item")


class StockItemUomLine(db.Model):
    __tablename__ = 'iwms_stock_item_uom_line'

    """ COLUMNS """
    id = db.Column(db.Integer, primary_key=True)
    stock_item_id = db.Column(db.Integer, db.ForeignKey('iwms_stock_item.id',ondelete='CASCADE'))
    uom_id = db.Column(db.Integer,db.ForeignKey('iwms_unit_of_measure.id',ondelete="SET NULL"),nullable=True)
    uom = db.relationship("UnitOfMeasure",backref='si_uom_line')
    qty = db.Column(db.Integer,nullable=True,default=0)
    barcode = db.Column(db.String(255),nullable=True,default="")
    default_cost = db.Column(db.Numeric(10,2),nullable=True,default=0)
    default_price = db.Column(db.Numeric(10,2),nullable=True,default=0)
    length = db.Column(db.String(255),nullable=True,default="")
    width = db.Column(db.String(255),nullable=True,default="")
    height = db.Column(db.String(255),nullable=True,default="")


class UnitOfMeasure(Base,Admin):
    __tablename__ = 'iwms_unit_of_measure'
    __amname__ = 'unit_of_measure'
    __amdescription__ = 'Unit Of Measure'
    __amicon__ = 'pe-7s-vector'

    """ COLUMNS """
    code = db.Column(db.String(64),nullable=False,unique=True)
    description = db.Column(db.String(255),nullable=True)


class Reason(Base,Admin):
    __tablename__ = 'iwms_reason'
    __amname__ = 'reason'
    __amdescription__ = 'Reason'
    __amicon__ = 'pe-7s-news-paper'

    """ COLUMNS """
    code = db.Column(db.String(64),nullable=False,unique=True)
    description = db.Column(db.String(255),nullable=True)
    type = db.Column(db.String(64),nullable=False)


class Source(Base,Admin):
    __tablename__ = 'iwms_source'
    __amname__ = 'source'
    __amdescription__ = 'Source'
    __amicon__ = 'pe-7s-news-paper'

    """ COLUMNS """
    name = db.Column(db.String(64),nullable=False)
    description = db.Column(db.String(255),nullable=True)


class StockReceipt(Base,Admin):
    __tablename__ = 'iwms_stock_receipt'
    __amname__ = 'stock_receipt'
    __amdescription__ = 'Stock Receipt'
    __amicon__ = 'pe-7s-news-paper'

    """ COLUMNS """
    sr_number = db.Column(db.String(255),nullable=True,default="")
    status = db.Column(db.String(255),nullable=True,default="")
    purchase_order_id = db.Column(db.Integer,db.ForeignKey('iwms_purchase_order.id',ondelete="SET NULL"),nullable=True)
    purchase_order = db.relationship('PurchaseOrder',backref='stockreceipt')
    warehouse_id = db.Column(db.Integer,db.ForeignKey('iwms_warehouse.id',ondelete="SET NULL"),nullable=True)
    warehouse = db.relationship('Warehouse',backref='stockreceipt')
    source_id = db.Column(db.Integer,db.ForeignKey('iwms_source.id',ondelete="SET NULL"),nullable=True)
    source = db.relationship('Source',backref='stockreceipt')
    supplier = db.Column(db.String(255),nullable=True,default="")
    reference = db.Column(db.String(255),nullable=True,default="")
    si_number = db.Column(db.String(255),nullable=True,default="")
    bol = db.Column(db.String(255),nullable=True,default="")
    remarks = db.Column(db.String(255),nullable=True,default="")
    date_received = db.Column(db.DateTime, default=datetime.utcnow,nullable=True)
    putaway_txn = db.Column(db.String(255),nullable=True,default="")
    item_line = db.relationship('StockReceiptItemLine', cascade='all,delete', backref="stock_receipt")

    
class StockReceiptItemLine(db.Model):
    __tablename__ = 'iwms_stock_receipt_item_line'

    """ COLUMNS """
    id = db.Column(db.Integer, primary_key=True)
    stock_receipt_id = db.Column(db.Integer, db.ForeignKey('iwms_stock_receipt.id',ondelete='CASCADE'))
    stock_item_id = db.Column(db.Integer,db.ForeignKey('iwms_stock_item.id',ondelete="SET NULL"),nullable=True)
    stock_item = db.relationship('StockItem',backref="sr_line")
    lot_no = db.Column(db.String(255),nullable=True,default="")
    expiry_date = db.Column(db.DateTime,nullable=True)
    uom = db.Column(db.String(255),nullable=True, default="")
    received_qty = db.Column(db.Integer,nullable=True,default=None)
    net_weight = db.Column(db.Integer,nullable=True,default=None)
    timestamp = db.Column(db.String(255),nullable=True)
    is_putaway = db.Column(db.Boolean,default=False)

class Putaway(Base,Admin):
    __tablename__ = 'iwms_putaway'
    __amname__ = 'putaway'
    __amdescription__ = 'Putaway'
    __amicon__ = 'pe-7s-junk'

    """ COLUMNS """
    pwy_number = db.Column(db.String(255),nullable=False)
    stock_receipt_id = db.Column(db.Integer,db.ForeignKey('iwms_stock_receipt.id',ondelete="SET NULL"),nullable=True)
    stock_receipt = db.relationship('StockReceipt',backref="putaway")
    status = db.Column(db.String(255),nullable=True)
    warehouse_id = db.Column(db.Integer,db.ForeignKey('iwms_warehouse.id',ondelete="SET NULL"),nullable=True)
    warehouse = db.relationship('Warehouse',backref='pwy_warehouse')
    reference = db.Column(db.String(255),nullable=True)
    remarks = db.Column(db.String(255),nullable=True)
    item_line = db.relationship('PutawayItemLine', cascade='all,delete', backref="putaway")


class PutawayItemLine(db.Model):
    __tablename__ = 'iwms_putaway_item_line'

    """ COLUMNS """
    id = db.Column(db.Integer, primary_key=True)
    putaway_id = db.Column(db.Integer, db.ForeignKey('iwms_putaway.id',ondelete='CASCADE'))
    stock_item_id = db.Column(db.Integer,db.ForeignKey('iwms_stock_item.id',ondelete="SET NULL"),nullable=True)
    stock_item = db.relationship('StockItem',backref="pwy_line")
    lot_no = db.Column(db.String(255),nullable=True,default="")
    expiry_date = db.Column(db.DateTime,nullable=True)
    uom = db.Column(db.String(255),nullable=True, default="")
    qty = db.Column(db.Integer,nullable=True,default=None)
    serials = db.Column(db.Integer,nullable=True,default=None)
    timestamp = db.Column(db.String(255),nullable=True)


class Supplier(Base,Admin):
    __tablename__ = 'iwms_supplier'
    __amname__ = 'supplier'
    __amdescription__ = 'Supplier'
    __amicon__ = 'pe-7s-server'

    """ COLUMNS """
    code = db.Column(db.String(255),nullable=False,unique=True)
    name = db.Column(db.String(255),nullable=False)
    status = db.Column(db.String(255),nullable=True)
    address = db.Column(db.String(255),nullable=True)
    email_address = db.Column(db.String(255),nullable=True)
    contact_number = db.Column(db.String(255),nullable=True)
    contact_person = db.Column(db.String(255),nullable=True)


class Term(Base,Admin):
    __tablename__  = 'iwms_term'
    __amname__ = 'term'
    __amdescription__ = 'Terms'
    __amicon__ = 'pe-7s-pen'

    """ COLUMNS """
    code = db.Column(db.String(255),nullable=False,unique=True)
    description = db.Column(db.String(255),nullable=True)
    days = db.Column(db.Integer,nullable=True)

    @property
    def name(self):
        return self.description

class ShipTo(enum.Enum):
    warehouse = "Warehouse"


class PurchaseOrder(Base,Admin):
    __tablename__ = 'iwms_purchase_order'
    __amname__ = 'purchase_order'
    __amdescription__ = 'Purchase Order'
    __amicon__ = 'pe-7s-wallet'

    """ COLUMNS """
    po_number = db.Column(db.String(255),nullable=False)
    status = db.Column(db.String(255),default="LOGGED")
    supplier_id = db.Column(db.Integer,db.ForeignKey('iwms_supplier.id',ondelete="SET NULL"),nullable=True)
    supplier = db.relationship('Supplier',backref="purchase_orders")
    ship_to = db.Column(db.Enum(ShipTo),default=ShipTo.warehouse)
    warehouse_id = db.Column(db.Integer,db.ForeignKey('iwms_warehouse.id',ondelete="SET NULL"),nullable=True)
    warehouse = db.relationship('Warehouse',backref="purchase_orders")
    address = db.Column(db.String(255),nullable=True)
    remarks = db.Column(db.String(255),nullable=True)
    ordered_date = db.Column(db.DateTime, default=datetime.utcnow,nullable=True)
    delivery_date = db.Column(db.DateTime, default=datetime.utcnow,nullable=True)
    approved_by = db.Column(db.String(255),nullable=True)
    product_line = db.relationship('PurchaseOrderProductLine', cascade='all,delete', backref="po")


class PurchaseOrderProductLine(db.Model):
    __tablename__ = 'iwms_purchase_order_product_line'

    """ COLUMNS """
    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('iwms_purchase_order.id',ondelete='CASCADE'))
    stock_item_id = db.Column(db.Integer,db.ForeignKey('iwms_stock_item.id',ondelete="SET NULL"),nullable=True)
    stock_item = db.relationship('StockItem',backref="po_line")
    qty = db.Column(db.Integer,nullable=True)
    unit_cost = db.Column(db.Numeric(10,2),nullable=True)
    amount = db.Column(db.Numeric(10,2),nullable=True)
    uom_id = db.Column(db.Integer,db.ForeignKey('iwms_unit_of_measure.id',ondelete="SET NULL"),nullable=True)
    uom = db.relationship("UnitOfMeasure",backref='po_line_uom')
    received_qty = db.Column(db.Integer,nullable=True)
    remaining_qty = db.Column(db.Integer,nullable=True)

class StockItemType(Base,Admin):
    __tablename__ = 'iwms_stock_item_type'
    __amname__ = 'stock_item_type'
    __amdescription__ = 'Stock Item Type'
    __amicon__ = 'pe-7s-network'

    """ COLUMNS """
    name = db.Column(db.String(255),nullable=False)


class TaxCode(Base,Admin):
    __tablename__ = 'iwms_tax_code'
    __amname__ = 'tax_code'
    __amdescription__ = 'Tax Code'

    """ COLUMNS """
    name = db.Column(db.String(255),nullable=False)


class ShipVia(Base,Admin):
    __tablename__ = 'iwms_ship_via'
    __amname__ = 'ship_via'
    __amdescription__ = 'Ship Via'
    __amicon__ = 'pe-7s-plane'

    """ COLUMNS """
    description = db.Column(db.String(255),nullable=False)

    @property
    def name(self):
        return self.description


class ClientGroup(Base,Admin):
    __tablename__ = 'iwms_client_group'
    __amname__ = 'client_group'
    __amdescription__ = 'Client Group'

    """ COLUMNS """
    name = db.Column(db.String(255),nullable=False)


class Client(Base,Admin):
    __tablename__ = 'iwms_client'
    __amname__ = 'client'
    __amdescription__ = 'Client'
    __amicon__ = 'pe-7s-global'

    """ COLUMNS """
    code = db.Column(db.String(255),nullable=False,unique=True)
    name = db.Column(db.String(255),nullable=True)
    ship_to = db.Column(db.String(255),nullable=True)
    term_id = db.Column(db.Integer,db.ForeignKey('iwms_term.id',ondelete="SET NULL"),nullable=True)
    term = db.relationship('Term',backref="clients")
    ship_via_id = db.Column(db.Integer,db.ForeignKey('iwms_ship_via.id',ondelete="SET NULL"),nullable=True)
    ship_via = db.relationship('ShipVia',backref="clients")

class ItemBinLocations(db.Model):
    __tablename__ = 'iwms_item_bin_locations'
    
    """ COLUMNS """
    id = db.Column(db.Integer, primary_key=True)
    inventory_item_id = db.Column(db.Integer,db.ForeignKey('iwms_inventory_item.id',ondelete="SET NULL"),nullable=True)
    bin_location_id = db.Column(db.Integer,db.ForeignKey('iwms_bin_location.id',ondelete="SET NULL"),nullable=True)
    inventory_item = db.relationship('InventoryItem', backref="item_bin_locations")
    bin_location = db.relationship('BinLocation', backref="item_bin_locations")
    qty_on_hand = db.Column(db.Integer,nullable=True)
    expiry_date = db.Column(db.DateTime,nullable=True)
    lot_no = db.Column(db.String(255),nullable=True)
    putaway_id = db.Column(db.Integer,db.ForeignKey('iwms_putaway.id',ondelete="SET NULL"),nullable=True)
    putaway = db.relationship('Putaway',backref='items')

class InventoryItem(Base,Admin):
    __tablename__ = 'iwms_inventory_item'
    __amname__ = 'inventory_item'
    __amdescription__ = 'Inventory Item'
    __amicon__ = 'pe-7s-download'
    
    """ COLUMNS """
    stock_item_id = db.Column(db.Integer,db.ForeignKey('iwms_stock_item.id',ondelete="SET NULL"),nullable=True)
    stock_item = db.relationship('StockItem',backref="inventory_stock_item")
    stock_item_type_id = db.Column(db.Integer,db.ForeignKey('iwms_stock_item_type.id',ondelete="SET NULL"),nullable=True)
    stock_item_type = db.relationship('StockItemType',backref='inventory_items')
    category_id = db.Column(db.Integer,db.ForeignKey('iwms_category.id',ondelete="SET NULL"),nullable=True)
    category = db.relationship('Category',backref='inventory_items')
    default_cost = db.Column(db.Numeric(10,2),nullable=True,default=None)
    default_price = db.Column(db.Numeric(10,2),nullable=True,default=None)

class SalesOrder(Base,Admin):
    __tablename__ = 'iwms_sales_order'
    __amname__ = 'sales_order'
    __amdescription__ = 'Sales Order'
    __amicon__ = 'pe-7s-cart'

    """ COLUMNS """
    number = db.Column(db.String(255),nullable=False)
    status = db.Column(db.String(255),default="LOGGED")
    client_id = db.Column(db.Integer,db.ForeignKey('iwms_client.id',ondelete="SET NULL"),nullable=True)
    client = db.relationship('Client',backref="sales_orders")
    ship_to = db.Column(db.String(255),nullable=True)
    end_user = db.Column(db.String(255),nullable=True)
    tax_info = db.Column(db.String(255),nullable=True)
    reference = db.Column(db.String(255),nullable=True)
    sales_representative = db.Column(db.String(255),nullable=True)
    inco_terms = db.Column(db.String(255),nullable=True)
    destination_port = db.Column(db.String(255),nullable=True)
    remarks = db.Column(db.String(255),nullable=True)
    term_id = db.Column(db.Integer,db.ForeignKey('iwms_term.id',ondelete="SET NULL"),nullable=True)
    term = db.relationship('Term',backref="sales_orders")
    ship_via_id = db.Column(db.Integer,db.ForeignKey('iwms_ship_via.id',ondelete="SET NULL"),nullable=True)
    ship_via = db.relationship('ShipVia',backref="sales_orders")
    ordered_date = db.Column(db.DateTime, default=datetime.utcnow,nullable=True)
    delivery_date = db.Column(db.DateTime, default=datetime.utcnow,nullable=True)
    approved_by = db.Column(db.String(255),nullable=True)
    active_picklist= db.Column(db.String(255),nullable=True)
    total_price = db.Column(db.Numeric(10,2),nullable=True)
    product_line = db.relationship('SalesOrderLine', cascade='all,delete', backref="sales_order")

class SalesOrderLine(db.Model):
    __tablename__ = 'iwms_sales_order_line'

    """ COLUMNS """
    id = db.Column(db.Integer, primary_key=True)
    sales_order_id = db.Column(db.Integer, db.ForeignKey('iwms_sales_order.id',ondelete='CASCADE'))
    inventory_item_id = db.Column(db.Integer,db.ForeignKey('iwms_inventory_item.id',ondelete="SET NULL"),nullable=True)
    inventory_item = db.relationship('InventoryItem',backref="so_line")
    item_bin_location_id = db.Column(db.Integer,db.ForeignKey('iwms_item_bin_locations.id',ondelete="SET NULL"),nullable=True)
    item_bin_location = db.relationship('ItemBinLocations',backref="so_line")
    qty = db.Column(db.Integer,nullable=True)
    issued_qty = db.Column(db.Integer,nullable=True)
    unit_price = db.Column(db.Numeric(10,2),nullable=True)
    uom_id = db.Column(db.Integer,db.ForeignKey('iwms_unit_of_measure.id',ondelete="SET NULL"),nullable=True)
    uom = db.relationship("UnitOfMeasure",backref='so_line_uom')


class Picking(Base,Admin):
    __tablename__ = 'iwms_picking'
    __amname__ = 'picking'
    __amdescription__ = 'Picking'
    __amicon__ = 'pe-7s-upload'

    """ COLUMNS """
    number = db.Column(db.String(255),nullable=False)
    status = db.Column(db.String(255),nullable=False)
    warehouse_id = db.Column(db.Integer,db.ForeignKey('iwms_warehouse.id',ondelete="SET NULL"),nullable=True)
    warehouse = db.relationship('Warehouse',backref="pickings")
    sales_order_id = db.Column(db.Integer,db.ForeignKey('iwms_sales_order.id',ondelete="SET NULL"),nullable=True)
    sales_order = db.relationship('SalesOrder',backref="pickings")
    remarks = db.Column(db.String(255),nullable=True)
    item_line = db.relationship('PickingItemLine', cascade='all,delete', backref="picking")


class PickingItemLine(db.Model):
    __tablename__ = 'iwms_picking_item_line'

    """ COLUMNS """
    id = db.Column(db.Integer, primary_key=True)
    picking_id = db.Column(db.Integer, db.ForeignKey('iwms_picking.id',ondelete='CASCADE'))
    item_bin_location_id = db.Column(db.Integer,db.ForeignKey('iwms_item_bin_locations.id',ondelete="SET NULL"),nullable=True)
    item_bin_location = db.relationship('ItemBinLocations',backref="pck_line")
    lot_no = db.Column(db.String(255),nullable=True,default="")
    expiry_date = db.Column(db.DateTime,nullable=True)
    uom = db.Column(db.String(255),nullable=True, default="")
    qty = db.Column(db.Integer,nullable=True,default=None)
    timestamp = db.Column(db.String(255),nullable=True)
