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
    name = db.Column(db.String(64),nullable=False)
    model_name = 'Groups'
    model_icon = 'pe-7s-users'
    model_description = "Groups"

class Department(Base,Admin):
    __tablename__ =  'iwms_department'
    name = db.Column(db.String(64),nullable=False)
    model_name = 'department'
    model_icon = 'pe-7s-culture'
    model_description = "Departments"

class TransactionType(Base,Admin):
    __tablename__ = 'iwms_transaction_type'
    code = db.Column(db.String(64),nullable=False)
    description = db.Column(db.String(255),nullable=True)
    prefix = db.Column(db.String(64),nullable=False)
    next_number_series = db.Column(db.Integer,nullable=True)
    model_name = 'transaction_type'
    model_icon = 'pe-7s-network'

class Email(Base,Admin):
    __tablename__ = 'iwms_email'
    email = db.Column(db.String(64),nullable=False)
    module_code = db.Column(db.String(64),nullable=False)
    description = db.Column(db.String(255),nullable=True)
    type = db.Column(db.String(64),nullable=False)
    model_name = 'email'
    model_icon = 'pe-7s-mail'

class Warehouse(Base,Admin):
    __tablename__ = 'iwms_warehouse'
    code = db.Column(db.String(64),nullable=False)
    name = db.Column(db.String(64),nullable=False)
    main_warehouse = db.Column(db.Boolean, nullable=False, default="0")
    bins = db.relationship('BinLocation',backref='warehouse')
    
    model_name = 'warehouse'
    model_icon = 'pe-7s-map'

class Zone(Base,Admin):
    __tablename__ = 'iwms_zone'
    code = db.Column(db.String(64),nullable=False)
    description = db.Column(db.String(255),nullable=True)

    @property
    def name(self):
        return self.code
        
    model_name = 'zone'
    model_icon = 'pe-7s-map-2'

class BinLocation(Base,Admin):
    __tablename__ = 'iwms_bin_location'
    code = db.Column(db.String(64),nullable=False)
    description = db.Column(db.String(255),nullable=True)
    index = db.Column(db.Integer,nullable=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('iwms_warehouse.id',ondelete="SET NULL"),nullable=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('iwms_zone.id',ondelete="SET NULL"),nullable=True)
    zone = db.relationship('Zone',backref='binlocationzone')
    pallet_slot = db.Column(db.Integer,default=0)
    pallet_cs = db.Column(db.Integer,default=0)
    capacity = db.Column(db.Integer,default=0)
    weight_cap = db.Column(db.Integer,default=0)
    cbm_cap = db.Column(db.Integer,default=0)

    model_name = 'bin_location'
    model_icon = 'pe-7s-map-marker'

class Category(Base,Admin):
    __tablename__ = 'iwms_category'
    code = db.Column(db.String(64),nullable=False)
    description = db.Column(db.String(255),nullable=True)

    model_name = 'category'
    model_icon = 'pe-7s-network'

class StockItemStatus(enum.Enum):
    active = "Active"
    hold = "Hold"

suppliers = db.Table('iwms_suppliers',
    db.Column('supplier_id', db.Integer, db.ForeignKey('iwms_supplier.id'), primary_key=True),
    db.Column('stock_item_id', db.Integer, db.ForeignKey('iwms_stock_item.id'), primary_key=True)
)

class StockItem(Base,Admin):
    __tablename__ = 'iwms_stock_item'
    number = db.Column(db.String(255),nullable=False)
    status = db.Column(db.Enum(StockItemStatus),default=StockItemStatus.active)
    stock_item_type_id = db.Column(db.Integer,db.ForeignKey('iwms_stock_item_type.id',ondelete="SET NULL"),nullable=True)
    stock_item_type = db.relationship('StockItemType',backref='type_stock_items')
    category_id = db.Column(db.Integer,db.ForeignKey('iwms_category.id',ondelete="SET NULL"),nullable=True)
    category = db.relationship('Category',backref='stockitem_category')
    has_serial = db.Column(db.Boolean,default="0")
    monitor_expiration = db.Column(db.Boolean,default="0")
    brand = db.Column(db.String(255),nullable=True,default="")
    name = db.Column(db.String(255),nullable=True,default="")
    description = db.Column(db.String(255),nullable=True,default="")
    cap_size = db.Column(db.Integer,nullable=True,default=0)
    cap_profile = db.Column(db.Integer,nullable=True,default=0)
    compound = db.Column(db.Integer,nullable=True,default=0)
    suppliers = db.relationship('Supplier', secondary=suppliers, lazy='subquery',backref=db.backref('stock_items', lazy=True))
    #TODO: clients = db.Column(db.String(255),nullable=True,default="")
    packaging = db.Column(db.String(255),nullable=True,default="")
    tax_code_id = db.Column(db.Integer,db.ForeignKey('iwms_tax_code.id',ondelete="SET NULL"),nullable=True)
    tax_code = db.relationship("TaxCode",backref='stock_items')
    reorder_qty = db.Column(db.Integer,nullable=True,default=0)
    description_plu = db.Column(db.String(255),nullable=True,default="")
    barcode = db.Column(db.String(255),nullable=True,default=None,unique=True)
    qty_plu = db.Column(db.Integer,nullable=True,default=0)
    length = db.Column(db.String(255),nullable=True,default="")
    width = db.Column(db.String(255),nullable=True,default="")
    height = db.Column(db.String(255),nullable=True,default="")
    unit_id = db.Column(db.Integer,db.ForeignKey('iwms_unit_of_measure.id',ondelete="SET NULL"),nullable=True)
    unit = db.relationship("UnitOfMeasure",backref='unit_stock_items')
    default_cost = db.Column(db.Numeric(10,2),nullable=True,default=0)
    default_price = db.Column(db.Numeric(10,2),nullable=True,default=0)
    weight = db.Column(db.String(255),nullable=True,default="")
    cbm = db.Column(db.String(255),nullable=True,default="")
    qty_per_pallet = db.Column(db.Integer,nullable=True,default=0)
    shelf_life = db.Column(db.Integer,nullable=True,default=0)
    qa_lead_time = db.Column(db.Integer,nullable=True,default=0)
    uom_line = db.relationship('StockItemUomLine', cascade='all,delete', backref="stock_item")

    model_name = 'stock_item'
    model_icon = 'pe-7s-download'


class StockItemUomLine(db.Model):
    __tablename__ = 'iwms_stock_item_uom_line'
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
    code = db.Column(db.String(64),nullable=False)
    description = db.Column(db.String(255),nullable=True)

    model_name = 'unit_of_measure'
    model_icon = 'pe-7s-vector'

class Reason(Base,Admin):
    __tablename__ = 'iwms_reason'
    code = db.Column(db.String(64),nullable=False)
    description = db.Column(db.String(255),nullable=True)
    type = db.Column(db.String(64),nullable=False)

    model_name = 'reason'
    model_icon = 'pe-7s-news-paper'

class StockReceiptSource(enum.Enum):
    purchase_order = "Purchase Order"
    stock_issuance = "Stock Issuance"
    rturn = "Return"
    ud = "Unscheduled Delivery"

class StockReceipt(Base,Admin):
    __tablename__ = 'iwms_stock_receipt'
    sr_number = db.Column(db.String(255),nullable=True,default="")
    status = db.Column(db.String(255),nullable=True,default="")
    warehouse_id = db.Column(db.Integer,db.ForeignKey('iwms_warehouse.id',ondelete="SET NULL"),nullable=True)
    warehouse = db.relationship('Warehouse',backref='stockreceipt')
    source = db.Column(db.Enum(StockReceiptSource),default=StockReceiptSource.purchase_order)
    po_number = db.Column(db.String(255),nullable=True,default="")
    supplier = db.Column(db.String(255),nullable=True,default="")
    reference = db.Column(db.String(255),nullable=True,default="")
    si_number = db.Column(db.String(255),nullable=True,default="")
    bol = db.Column(db.String(255),nullable=True,default="")
    remarks = db.Column(db.String(255),nullable=True,default="")
    date_received = db.Column(db.DateTime, default=datetime.utcnow,nullable=True)
    putaway_txn = db.Column(db.String(255),nullable=True,default="")
    item_line = db.relationship('StockReceiptItemLine', cascade='all,delete', backref="stock_receipt")

    model_name = 'stock_receipt'
    model_icon = 'pe-7s-news-paper'
    
class StockReceiptItemLine(db.Model):
    __tablename__ = 'iwms_stock_receipt_item_line'
    id = db.Column(db.Integer, primary_key=True)
    stock_receipt_id = db.Column(db.Integer, db.ForeignKey('iwms_stock_receipt.id',ondelete='CASCADE'))
    stock_item_id = db.Column(db.Integer,db.ForeignKey('iwms_stock_item.id',ondelete="SET NULL"),nullable=True)
    stock_item = db.relationship('StockItem',backref="sr_line")
    lot_no = db.Column(db.String(255),nullable=True,default="")
    expiry_date = db.Column(db.DateTime,nullable=True)
    uom = db.Column(db.String(255),nullable=True, default="")
    received_qty = db.Column(db.Integer,nullable=True,default=None)
    net_weight = db.Column(db.Integer,nullable=True,default=None)
    timestamp = db.Column(db.String(255),nullable=True,default="")


class Putaway(Base,Admin):
    __tablename__ = 'iwms_putaway'
    pwy_number = db.Column(db.String(255),nullable=False)
    status = db.Column(db.String(255),nullable=True)
    warehouse_id = db.Column(db.Integer,db.ForeignKey('iwms_warehouse.id',ondelete="SET NULL"),nullable=True)
    warehouse = db.relationship('Warehouse',backref='pwy_warehouse')
    receipt_no = db.Column(db.String(255),nullable=True)
    reference = db.Column(db.String(255),nullable=True)
    remarks = db.Column(db.String(255),nullable=True)
    model_name = 'putaway'
    model_icon = 'pe-7s-junk'

class Supplier(Base,Admin):
    __tablename__ = 'iwms_supplier'

    code = db.Column(db.String(255),nullable=False)
    name = db.Column(db.String(255),nullable=False)
    status = db.Column(db.String(255),nullable=True)
    address = db.Column(db.String(255),nullable=True)
    email_address = db.Column(db.String(255),nullable=True)
    contact_number = db.Column(db.String(255),nullable=True)
    contact_person = db.Column(db.String(255),nullable=True)

    model_name = 'supplier'
    model_icon = ''

class Term(Base,Admin):
    __tablename__  = 'iwms_term'
    code = db.Column(db.String(255),nullable=False)
    description = db.Column(db.String(255),nullable=True)
    days = db.Column(db.Integer,nullable=True)

    model_name = 'term'
    model_icon = ''

class ShipTo(enum.Enum):
    warehouse = "Warehouse"


class PurchaseOrderStatus(enum.Enum):
    LOGGED = "LOGGED"
    RELEASED = "RELEASED"
    COMPLETED = "COMPLETED"

class PurchaseOrder(Base,Admin):
    __tablename__ = 'iwms_purchase_order'
    po_number = db.Column(db.String(255),nullable=False)
    status = db.Column(db.Enum(PurchaseOrderStatus),default=PurchaseOrderStatus.LOGGED)
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

    model_name = 'purchase_order'
    model_icon = 'pe-7s-wallet'

class PurchaseOrderProductLine(db.Model):
    __tablename__ = 'iwms_purchase_order_product_line'
    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('iwms_purchase_order.id',ondelete='CASCADE'))
    stock_item_id = db.Column(db.Integer,db.ForeignKey('iwms_stock_item.id',ondelete="SET NULL"),nullable=True)
    stock_item = db.relationship('StockItem',backref="po_line")
    qty = db.Column(db.Integer,nullable=True)
    unit_cost = db.Column(db.Numeric(10,2),nullable=True)
    amount = db.Column(db.Numeric(10,2),nullable=True)
    uom_id = db.Column(db.Integer,db.ForeignKey('iwms_unit_of_measure.id',ondelete="SET NULL"),nullable=True)
    uom = db.relationship("UnitOfMeasure",backref='po_line_uom')

class StockItemType(Base,Admin):
    __tablename__ = 'iwms_stock_item_type'
    name = db.Column(db.String(255),nullable=False)
    model_name = 'stock_item_type'
    model_icon = ''

class TaxCode(Base,Admin):
    __tablename__ = 'iwms_tax_code'
    name = db.Column(db.String(255),nullable=False)