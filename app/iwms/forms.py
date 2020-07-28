from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField,IntegerField, DecimalField, SelectField,DateTimeField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from app.admin.forms import AdminIndexForm,AdminEditForm, AdminInlineForm, AdminField
from datetime import datetime


class GroupForm(AdminIndexForm):
    index_headers = ['Group Name','active']
    index_title = "Groups"
    index_message = "User groups"

    name = AdminField(label="Name",validators=[DataRequired()])

    def create_fields(self):
        return [
            [self.name]
            ]

class GroupEditForm(AdminEditForm):
    name = AdminField(label='Name', validators=[DataRequired()])
    
    def edit_fields(self):
        return [[self.name]]

    edit_title = "Edit group"

class EmailEditForm(AdminEditForm):
    email = AdminField(label='Email Address',input_type='email',validators=[DataRequired()])
    module_code = AdminField(label="Module Code",validators=[DataRequired()])
    description = AdminField(label="Description",required=False)
    type = AdminField(label='Type',validators=[DataRequired()])

    def edit_fields(self):
        return [
            [self.email,self.module_code],
            [self.description,self.type]
        ]
    edit_title = 'Edit email address'

class DepartmentEditForm(AdminEditForm):
    name = AdminField(label="Name",validators=[DataRequired()])

    def edit_fields(self):
        return [
            [self.name]
        ]
    edit_title = 'Edit department'

class TransactionTypeEditForm(AdminEditForm):
    code = AdminField(label='Code',validators=[DataRequired()])
    description = AdminField(label='Description',required=False)
    prefix = AdminField(label='Prefix',validators=[DataRequired()])
    next_number_series =AdminField(label='Next Number Series',required=False)
    
    def edit_fields(self):
        return [
            [self.code,self.description],
            [self.prefix,self.next_number_series]
            ]
    edit_title = 'Edit transaction type'    

class WarehouseEditForm(AdminEditForm):
    code = AdminField(label='Code',validators=[DataRequired()])
    name = AdminField(label='Name',validators=[DataRequired()])
    active = AdminField(label='Active Flag',required=False,input_type='checkbox')
    main_warehouse = AdminField(label="Main Warehouse",required=False,input_type='checkbox')
    
    def edit_fields(self):
        return [
            [self.code,self.name],[self.active,self.main_warehouse]
        ]
    edit_title = 'Edit warehouse'

class ZoneEditForm(AdminEditForm):
    code = AdminField(label='Code',validators=[DataRequired()])
    description = AdminField(label='Description',validators=[DataRequired()])

    def edit_fields(self):
        return [[
            self.code,self.description
        ]]    
    edit_title = 'Edit zone'

class BinLocationEditForm(AdminEditForm):
    from .models import BinLocation,Zone

    code = AdminField(label='Code',validators=[DataRequired()])
    description = AdminField(label='Description',validators=[DataRequired()])
    index = AdminField(label='Index',required=False)
    warehouse_id = AdminField(label='Warehouse',required=False,model=BinLocation)
    zone_id = AdminField(label='Zone',required=False,model=Zone)
    pallet_slot = AdminField(label='Pallet Slot',required=False)
    pallet_cs = AdminField(label='Pallet CS',required=False)
    capacity = AdminField(label='Capacity',required=False)
    weight_cap = AdminField(label='Weight Cap',required=False)
    cbm_cap = AdminField(label='CBM Cap',required=False)

    def edit_fields(self):
        return [
            [self.code,self.description,self.index],
            [self.warehouse_id,self.zone_id],
            [self.pallet_slot,self.pallet_cs],
            [self.capacity,self.weight_cap,self.cbm_cap]
            ]
    edit_title = 'Edit Bin Location'

class CategoryEditForm(AdminEditForm):
    code = AdminField(label='Code',validators=[DataRequired()])
    description = AdminField(label='Description',validators=[DataRequired()])
    
    def edit_fields(self):
        return [
            [self.code,self.description]
        ]

    edit_title = 'Edit category'

class UnitOfMeasureEditForm(AdminEditForm):
    code = AdminField(label='Code',validators=[DataRequired()])
    description = AdminField(label='Description',validators=[DataRequired()])
    active = AdminField(label='Active',required=False,input_type='checkbox')

    def edit_fields(self):
        return [
            [self.code,self.description],[self.active]
        ]

    edit_title = 'Edit unit of measure'

class ReasonEditForm(AdminEditForm):
    code = AdminField(label='Code',validators=[DataRequired()])
    description = AdminField(label='Description',validators=[DataRequired()])
    type = AdminField(label='type',validators=[DataRequired()])

    def edit_fields(self):
        return [
            [self.code,self.type],[self.description]
        ]    
    edit_title = 'Edit reasons'

class EmailForm(AdminIndexForm):
    index_headers = ['Module Code','Description','Type','Email Address']
    index_title = "Email Addresses"
    index_message = "User groups"

    email = AdminField(label='Email Address',input_type='email',validators=[DataRequired()])
    module_code = AdminField(label="Module Code",validators=[DataRequired()])
    description = AdminField(label="Description",required=False)
    type = AdminField(label='Type',validators=[DataRequired()])

    def create_fields(self):
        return [[self.email,self.module_code],[self.description,self.type]]

class DepartmentForm(AdminIndexForm):
    index_headers = ['Name']
    index_title = 'Departments'
    
    name = AdminField(label="Name",validators=[DataRequired()])

    def create_fields(self):
        return [[self.name]]
    

class TransactionTypeForm(AdminIndexForm):
    index_headers = ['Code','Description','Prefix','Next Number Series']
    index_title = 'Transaction Types'

    code = AdminField(label='Code',validators=[DataRequired()])
    description = AdminField(label='Description',required=False)
    prefix = AdminField(label='Prefix',validators=[DataRequired()])
    next_number_series =AdminField(label='Next Number Series',required=False)
    
    def create_fields(self):
        return [[self.code,self.description],[self.prefix,self.next_number_series]]

class WarehouseForm(AdminIndexForm):
    index_headers = ['Code','Name','Active Flag','Main Warehouse','updated by','updated date']
    index_title = 'Warehouses'

    code = AdminField(label='Code',validators=[DataRequired()])
    name = AdminField(label='Name',validators=[DataRequired()])
    active = AdminField(label='Active Flag',required=False,input_type='checkbox')
    main_warehouse = AdminField(label="Main Warehouse",required=False,input_type='checkbox')
    
    def create_fields(self):
        return [[self.code,self.name],[self.active,self.main_warehouse]]
    
class ZoneForm(AdminIndexForm):
    index_headers = ['Code','Description']
    index_title = 'Zones'

    code = AdminField(label='Code',validators=[DataRequired()])
    description = AdminField(label='Description',validators=[DataRequired()])

    def create_fields(self):
        return [[self.code,self.description]]
    
class BinLocationForm(AdminIndexForm):
    from .models import BinLocation,Zone

    index_headers = [
        'Index','Code','Description','Warehouse',
        'Zone','Pallet Slot','Pallet CS','Capacity',
        'weight cap','cbm cap'
        ]
    index_title = 'Bin Locations'

    code = AdminField(label='Code',validators=[DataRequired()])
    description = AdminField(label='Description',validators=[DataRequired()])
    index = AdminField(label='Index',required=False)
    warehouse_id = AdminField(label='Warehouse',required=False,model=BinLocation)
    zone_id = AdminField(label='Zone',required=False,model=Zone)
    pallet_slot = AdminField(label='Pallet Slot',required=False)
    pallet_cs = AdminField(label='Pallet CS',required=False)
    capacity = AdminField(label='Capacity',required=False)
    weight_cap = AdminField(label='Weight Cap',required=False)
    cbm_cap = AdminField(label='CBM Cap',required=False)

    def create_fields(self):
        return [
            [self.code,self.description,self.index],
            [self.warehouse_id,self.zone_id],
            [self.pallet_slot,self.pallet_cs],
            [self.capacity,self.weight_cap,self.cbm_cap]
            ]

class CategoryForm(AdminIndexForm):
    index_headers = ['code','description']
    index_title = 'Categories'
    
    code = AdminField(label='Code',validators=[DataRequired()])
    description = AdminField(label='Description',validators=[DataRequired()])

    def create_fields(self):
        return [[self.code,self.description]]

class UnitOfMeasureForm(AdminIndexForm):
    index_headers = ['code','description','active']
    index_title = 'Unit of Measurements'
    
    code = AdminField(label='Code',validators=[DataRequired()])
    description = AdminField(label='Description',validators=[DataRequired()])
    active = AdminField(label='Active',required=False,input_type='checkbox')

    def create_fields(self):
        return [[self.code,self.description],[self.active]]

class ReasonForm(AdminIndexForm):
    index_headers = ['code','type','description']
    index_title = 'Reasons'
    
    code = AdminField(label='Code',validators=[DataRequired()])
    description = AdminField(label='Description',validators=[DataRequired()])
    type = AdminField(label='type',validators=[DataRequired()])

    def create_fields(self):
        return [[self.code,self.description],[self.type]]

class StockItemCreateForm(FlaskForm):
    number = AdminField(label='number')
    status = AdminField(label='status',required=False)
    stock_item_type_id = AdminField(label='stock_item_type_id',required=False)
    category_id = AdminField(label='category_id',required=False)
    has_serial = AdminField(label='has_serial',required=False)
    monitor_expiration = AdminField(label='monitor_expiration',required=False)
    brand = AdminField(label='brand',required=False)
    name = AdminField(label='name',required=False)
    description = AdminField(label='description',required=False)
    packaging = AdminField(label='packaging',required=False)
    tax_code_id = AdminField(label='tax_code_id',required=False)
    reorder_qty = AdminField(label='reorder_qty',required=False)
    description_plu = AdminField(label='description_plu',required=False)
    barcode = AdminField(label='barcode',required=False)
    qty_plu = AdminField(label='qty_plu',required=False)
    length = AdminField(label='length',required=False)
    width = AdminField(label='width',required=False)
    height = AdminField(label='height',required=False)
    unit_id = AdminField(label='unit_id',required=False)
    default_cost = AdminField(label='default_cost',required=False)
    default_price = AdminField(label='default_price',required=False)
    weight = AdminField(label='weight',required=False)
    cbm = AdminField(label='cbm',required=False)
    qty_per_pallet = AdminField(label='qty_per_pallet',required=False)
    shelf_life = AdminField(label='shelf_life',required=False)
    qa_lead_time = AdminField(label='qa_lead_time',required=False)

class StockItemView(AdminIndexForm):
    index_headers = ['SI No.','Name','Description']
    index_title = 'Stock Items'
    number = AdminField(label='SI No.')
    name = AdminField(label='Name',required=False)
    description = AdminField(label='Description',required=False)
    
    def create_fields(self):
        return [[self.number],[self.name,self.description]]

class PurchaseOrderViewForm(AdminIndexForm):
    index_headers = ['Po no.','date created','created by','status']
    index_title = 'Purchase Orders'
    po_number = AdminField(label='PO No.')
    status = AdminField(label="Status")

    def create_fields(self):
        return [[self.po_number,self.status]]

class StockReceiptCreateForm(FlaskForm):
    status = StringField('Status')
    warehouse_id = AdminField(label='warehouse',required=False)
    source = SelectField('Source',choices=[
        ('purchase_order','Purchase Order'),
        ('stock_issuance','Stock Issuance'),
        ('rturn','Return'),('ud','Unscheduled Delivery')])
    po_number = StringField('PO No.')
    supplier = StringField('Supplier')
    reference = StringField('Reference')
    si_number = StringField('SI Number')
    bol = StringField('BOL')
    remarks = StringField('Remarks')
    date_received = StringField(default=datetime.today)
    putaway_txn = StringField('Putaway Txn')

class PutawayCreateForm(FlaskForm):
    pwy_number = StringField()
    status = StringField()
    warehouse_id = IntegerField('Warehouse')
    receipt_no = StringField()
    reference = StringField()
    remarks = StringField()

class PurchaseOrderCreateForm(FlaskForm):
    po_number = StringField()
    status = StringField()
    supplier_id = StringField()
    ship_to = SelectField('Ship To',choices=[
        ('warehouse','Warehouse')])
    warehouse_id = StringField()
    address = StringField()
    ordered_date = StringField()
    delivery_date = StringField()
    approved_by = StringField()
    remarks = StringField()

class SupplierForm(AdminIndexForm):
    index_headers = ['code','name','status']
    index_title = 'Suppliers'
    
    code = AdminField(label='Code',validators=[DataRequired()],readonly=True)
    name = AdminField(label='Name',validators=[DataRequired()])
    address = AdminField(label='Address',required=False)
    email_address = AdminField(label='Email Address',required=False,input_type='email')
    contact_number = AdminField(label='Contact Number',required=False)
    contact_person = AdminField(label='Contact Person',required=False)
    def create_fields(self):
        return [[self.code,self.name],[self.address,self.email_address],[self.contact_number,self.contact_person]]


class SupplierEditForm(AdminEditForm):
    code = AdminField(label='Code',validators=[DataRequired()])
    name = AdminField(label='Name',validators=[DataRequired()])
    address = AdminField(label='Address',required=False)
    email_address = AdminField(label='Email Address',required=False,input_type='email')
    contact_number = AdminField(label='Contact Number',required=False)
    contact_person = AdminField(label='Contact Person',required=False)

    def edit_fields(self):
        return [[self.code,self.name],[self.address,self.email_address],[self.contact_number,self.contact_person]]
   
    edit_title = 'Edit supplier'


class TypeForm(AdminIndexForm):
    index_headers = ['name','created by','created at']
    index_title = 'Types'
    
    name = AdminField(label='Name',validators=[DataRequired()])

    def create_fields(self):
        return [[self.name]]

class TypeEditForm(AdminEditForm):
    name = AdminField(label='Name',validators=[DataRequired()])
    def edit_fields(self):
        return [[self.name]]
   
    edit_title = 'Edit type'
