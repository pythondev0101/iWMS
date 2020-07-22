from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField,IntegerField, DecimalField, SelectField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from app.admin.forms import AdminIndexForm,AdminEditForm, AdminInlineForm, AdminField


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

    def edit_fields(self):
        return [
            [self.code,self.description]
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
    index_headers = ['code','description']
    index_title = 'Unit of Measurements'
    
    code = AdminField(label='Code',validators=[DataRequired()])
    description = AdminField(label='Description',validators=[DataRequired()])

    def create_fields(self):
        return [[self.code,self.description]]

class ReasonForm(AdminIndexForm):
    index_headers = ['code','type','description']
    index_title = 'Reasons'
    
    code = AdminField(label='Code',validators=[DataRequired()])
    description = AdminField(label='Description',validators=[DataRequired()])
    type = AdminField(label='type',validators=[DataRequired()])

    def create_fields(self):
        return [[self.code,self.description],[self.type]]

class StockItemCreateForm(FlaskForm):
    from .models import Category
    number = StringField('No.')
    status = SelectField('Status',choices=[('active','Active'),('hold','Hold')])
    type = SelectField('Type',choices=[('part','Part')])
    category_id = AdminField(label='Category',required=False,model=Category)
    brand = StringField('Brand')
    name = StringField('Name')
    description = StringField('Description')
    packaging = StringField('Packaging')
    tax_code = SelectField('Tax Code',choices=[('test','TestCode')])
    reorder_qty = IntegerField('Reorder Qty')
    description_plu = StringField('Description')
    barcode = StringField('Barcode')
    length = StringField('Length')
    width = StringField('Width')
    height = StringField('Height')
    default_cost = DecimalField('Default Cost')
    default_price = DecimalField('Default Price')
    weight = StringField('Weight')
    cbm = StringField('CBM')
    qty_per_pallet = IntegerField('Qty per Pallet')
    shelf_life = IntegerField('Shelf Life(in months)')
    qa_lead_time = IntegerField('QA Lead Time(in hours)')

class StockReceiptCreateForm(FlaskForm):
    sr_number = StringField('Sr No.',validators=[DataRequired()])
    status = StringField('Status')
    warehouse_id = IntegerField('Warehouse')
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
    date_received = StringField('Date Received')
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

class SupplierForm(AdminIndexForm):
    index_headers = ['code','name','status']
    index_title = 'Suppliers'
    
    code = AdminField(label='Code',validators=[DataRequired()])
    name = AdminField(label='Name',validators=[DataRequired()])

    def create_fields(self):
        return [[self.code,self.name]]


class SupplierEditForm(AdminEditForm):
    code = AdminField(label='Code',validators=[DataRequired()])
    name = AdminField(label='Name',validators=[DataRequired()])

    def edit_fields(self):
        return [[self.code,self.name]]
   
    edit_title = 'Edit supplier'

class ProductForm(AdminIndexForm):
    index_headers = ['item no.','item name','description']
    index_title = 'Products'
    
    item_no = AdminField(label='Item No.',validators=[DataRequired()])
    item_name = AdminField(label='Item name',validators=[DataRequired()])
    description = AdminField(label='Description',required=False)
    barcode = AdminField(label='Barcode',required=False)

    def create_fields(self):
        return [[self.item_no,self.item_name],[self.description,self.barcode]]

class ProductEditForm(AdminEditForm):
    item_no = AdminField(label='Item No.',validators=[DataRequired()])
    item_name = AdminField(label='Item name',validators=[DataRequired()])
    description = AdminField(label='Description',required=False)
    barcode = AdminField(label='Barcode',required=False)

    def edit_fields(self):
        return [[self.item_no,self.item_name],[self.description,self.barcode]]
    
    edit_title = 'Edit product'