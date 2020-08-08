""" ROUTES """

""" FLASK IMPORTS """
from flask import render_template, flash, redirect, url_for, request, jsonify, current_app, send_from_directory
from flask_login import current_user, login_required
"""--------------END--------------"""

""" APP IMPORTS  """
from app.iwms import bp_iwms
from app import db, mail

"""--------------END--------------"""

from app import context
from app.admin.routes import admin_index, admin_edit

from .models import Group,Department,TransactionType,Warehouse,Zone, \
    BinLocation,Category,StockItem,UnitOfMeasure,Reason,StockReceipt,Putaway, \
        Email as EAddress, PurchaseOrder, Supplier, Term,PurchaseOrderProductLine,StockItemType,TaxCode,\
            StockItemUomLine,StockReceiptItemLine, PutawayItemLine,Source, SalesVia, ClientGroup, Client

from .forms import *
from datetime import datetime
from app.core.models import CoreLog
from app.auth.models import User
import pdfkit
from flask_mail import Message


"""----------------------INTERNAL FUNCTIONS-------------------------"""

def _generate_number(prefix, lID):
    generated_number = ""
    if 1 <= lID < 10:
        generated_number = prefix +"0000000" + str(lID+1)
    elif 10 <= lID < 100:
        generated_number = prefix + "000000" + str(lID+1)
    elif 100 <= lID < 1000:
        generated_number = prefix + "00000" + str(lID+1)
    elif 1000 <= lID < 10000:
        generated_number = prefix + "0000" + str(lID+1)
    elif 10000 <= lID < 100000:
        generated_number = prefix + "000" + str(lID+1)
    elif 100000 <= lID < 1000000:
        generated_number = prefix + "00" + str(lID+1)
    elif 1000000 <= lID < 10000000:
        generated_number = prefix + "0" + str(lID+1)
    else:
        generated_number = prefix + str(lID+1)
    return generated_number

def _check_create(model_name):
    #TODO: Temporary lang to pang check, maganda sana gawing decorator siguro 
    if current_user.is_superuser:
        return True
    else:
        user = User.query.get(current_user.id)
        for perm in user.permissions:
            if model_name == perm.model.name:
                if not perm.create:
                    return False
        return False

def _log_create(description,data):
    log = CoreLog()
    log.user_id = current_user.id
    log.date = datetime.utcnow()
    log.description = description
    log.data = data
    db.session.add(log)
    db.session.commit()
    print("Log created!")

def _makePOPDF(vendor,line_items):
    total = 0
    html = """<html><head><style>
    #invoice-POS{box-shadow: 0 0 1in -0.25in rgba(0, 0, 0, 0.5);padding:2mm;margin: 0 auto;width: 50%;background: #FFF;}
    ::selection {background: #f31544; color: #FFF;}
    ::moz-selection {background: #f31544; color: #FFF;}
    h1{font-size: 1.5em;color: #222;}
    h2{font-size: .9em;}
    h3{font-size: 1.2em;font-weight: 300;line-height: 2em;}
    p{font-size: .7em;color: #666;line-height: 1.2em;}
    #top, #mid,#bot{ /* Targets all id with 'col-' */border-bottom: 1px solid #EEE;}
    #mid{min-height: 80px;} 
    #bot{ min-height: 50px;}
    /*#top .logo{//float: left;height: 60px;width: 60px;background: url(http://michaeltruong.ca/images/logo1.png) no-repeat;background-size: 60px 60px;}*/
    /*.clientlogo{float: left;height: 60px;width: 60px;background: url(http://michaeltruong.ca/images/client.jpg) no-repeat;background-size: 60px 60px;border-radius: 50px;}*/
    .info{display: block;//float:left;margin-left: 0;}
    .title{float: right;}.title p{text-align: right;} 
    table{width: 100%;border-collapse: collapse;}
    td{//padding: 5px 0 5px 15px;//border: 1px solid #EEE}
    .tabletitle{//padding: 5px;font-size: .5em;background: #EEE;}
    .service{border-bottom: 1px solid #EEE;}
    .item{width: 24mm;}
    .itemtext{font-size: .5em;}
    #legalcopy{margin-top: 5mm;}
    </style>
    </head>
    <body><div id="invoice-POS">
    <center id="top"><div class="info">
    <h2>Purchase Order</h2></div><!--End Info-->
    </center><!--End InvoiceTop-->
    
    <div id="mid">
      <div class="info">
        <h2>Vendor</h2>"""
    html = html + """<p> 
            Company Name : {name}</br>
            Address : {add}</br>
            Email   : {email}</br>
            Phone   : {phone}</br>
        </p>""".format(name=vendor.name,add=vendor.address,email=vendor.email_address,phone=vendor.contact_number)
    
    html = html + """</div>
    </div><!--End Invoice Mid-->
    <div id="bot">
    <div id="table">
    <table>
    <tr class="tabletitle">
    <td class="item"><h2>Item</h2></td>
    <td class="item"><h2>Description</h2></td>
    <td class="Hours"><h2>Qty</h2></td>
    <td class="Hours"><h2>Unit Price</h2></td>
    <td class="Rate"><h2>Total</h2></td></tr>
    """

    for line in line_items:
        html = html + """
            <tr class='service'><td class='tableitem'><p class='itemtext'>{no}</p></td>
            <td class="tableitem"><p class="itemtext">{desc}</p></td>
            <td class="tableitem"><p class="itemtext">{qty}</p></td>
            <td class="tableitem"><p class="itemtext">{price}</p></td>
            <td class="tableitem"><p class="itemtext">{amount}</p></td>
            </tr>""".format(no=line.stock_item.number,desc=line.stock_item.description,\
                qty=line.qty,price=line.unit_cost,amount=line.amount)
        total = total + line.amount

    html = html + """
    <tr class="tabletitle">
    <td></td><td></td><td></td>
    <td class="Rate"><h2>Total</h2></td>
    <td class="payment"><h2>{total}</h2></td>
    </tr>
    </table>
    </div><!--End Table-->
    <div id="legalcopy">
    <p class="legal" style="text-align: center;">
    If you have any question about this purchase order,please contact
	</p>
    </div>
    </div><!--End InvoiceBot-->
    </div><!--End Invoice-->
    </body></html>
    """.format(total=total)
    return html


"""----------------------APIs-------------------------"""

@bp_iwms.route('/_update_bin_coord', methods=['POST'])
def _update_bin_coord():
    if request.method == 'POST':
        _bin_code = request.json['bin_code']
        _x,_y = request.json['x'], request.json['y']
        print(_x,_y);
        _bin = BinLocation.query.filter_by(code=_bin_code).first()
        print(_bin)
        _bin.x,_bin.y = _x, _y
        db.session.commit()
        return jsonify({'Result':True})

@bp_iwms.route('/_get_po_line',methods=["POST"])
def _get_po_line():
    if request.method == "POST":
        po_id = request.json['po_id']
        po = PurchaseOrder.query.get_or_404(po_id)
        po_line = []
        for line in po.product_line:
            po_line.append({
                'id':line.stock_item.id,'name':line.stock_item.name,
                'uom':line.uom.code if line.uom is not None else '',
                'number':line.stock_item.number,
                'qty':line.qty
                })
        print("test",po_line)
        res = jsonify(items=po_line)
        res.status_code = 200
        return res

@bp_iwms.route('/_get_sr_line',methods=["POST"])
def _get_sr_line():
    if request.method == "POST":
        sr_id = request.json['sr_id']
        sr = StockReceipt.query.get_or_404(sr_id)
        sr_line = []
        for line in sr.item_line:
            if line:
                _expiry_date = ''
                if line.expiry_date is not None:
                    _expiry_date = line.expiry_date.strftime("%Y-%m-%d")
                sr_line.append({
                    'id':line.stock_item.id,'name':line.stock_item.name,
                    'uom':line.uom,'number':line.stock_item.number,
                    'lot_no':line.lot_no,'expiry_date': _expiry_date,
                    'received_qty':line.received_qty
                    })
        res = jsonify(items=sr_line)
        res.status_code = 200
        return res

@bp_iwms.route('/_get_uom_line',methods=['POST'])
def _get_uom_line():
    if request.method == 'POST':
        stock_item_id = request.json['stock_item_id']
        obj = StockItem.query.get_or_404(stock_item_id)
        uom_line = []
        for line in obj.uom_line:
            default = "false"
            if line.uom_id == obj.unit_id:
                default = 'true'
            uom_line.append({'id':line.uom_id,'code':line.uom.code,'default':default})
        res = jsonify(uom_lines=uom_line)
        res.status_code = 200
        return res

@bp_iwms.route('/_barcode_check', methods=['POST'])
def _barcode_check():
    if request.method == 'POST':
        barcode = request.json['barcode']
        check = StockItem.query.filter(StockItem.barcode == barcode).first()
        if check:
            resp = jsonify(result=0)
            resp.status_code = 200
            return resp
        else:
            resp = jsonify(result=1)
            resp.status_code = 200
            return resp


"""----------------------ROUTE FUNCTIONS-------------------------"""

@bp_iwms.route('/')
@bp_iwms.route('/dashboard')
@login_required
def dashboard():
    context['module'] = 'iwms'
    context['active'] = 'main_dashboard'
    context['mm-active'] = ""
    return render_template('iwms/iwms_dashboard.html',context=context,title="Dashboard")

@bp_iwms.route('/bin_location')
@login_required
def warehouse_bin_location():
    context['active'] = 'warehouse_bin_location'
    context['mm-active'] = 'warehouse_bin_location'
    context['module'] = 'iwms'
    context['model'] = 'warehouse_bin_location'
    bins = BinLocation.query.all()
    return render_template('iwms/iwms_warehouse_bin_location.html',context=context,bins=bins)

@bp_iwms.route('/users')
@login_required
def users():
    from app.auth.routes import index
    # TODO: context['mm-active'] para lang sa gui ilagay na to sa admin index at edit,dapat wala dito to
    context['mm-active'] = 'Users'
    return index(template='iwms/iwms_index.html',active='system',edit_url='bp_iwms.iwms_user_edit',create_url='bp_iwms.iwms_user_create')

@bp_iwms.route('/user_edit/<int:oid>', methods=['GET', 'POST'])
def iwms_user_edit(oid):
    from app.auth.routes import user_edit
    context['mm-active'] = 'Users'
    return user_edit(oid=oid,template='iwms/iwms_edit.html',active='system',update_url='bp_iwms.iwms_user_edit')

@bp_iwms.route('/user_create/',methods=['POST'])
def iwms_user_create():
    from app.auth.routes import user_create
    context['mm-active'] = 'Users'
    return user_create(url='bp_iwms.users')

@bp_iwms.route('/groups')
@login_required
def groups():
    fields = [Group.id,Group.name,Group.active]
    context['mm-active'] = 'Groups'
    return admin_index(Group,fields=fields,create_url='bp_iwms.group_create',edit_url='bp_iwms.group_edit' , \
        form=GroupForm(),template="iwms/iwms_index.html",kwargs={'active':'system'})

@bp_iwms.route('/group_create',methods=['POST'])
@login_required
def group_create():
    if _check_create('Groups'):
        form = GroupForm()
        if request.method == "POST":
            if form.validate_on_submit():
                group = Group()
                group.name = form.name.data
                group.created_by = "{} {}".format(current_user.fname,current_user.lname)
                db.session.add(group)
                db.session.commit()
                flash('New group added successfully!','success')
                _log_create('New group added',"GroupID={}".format(group.id))
                return redirect(url_for('bp_iwms.groups'))
            else:
                for key, value in form.errors.items():
                    flash(str(key) + str(value), 'error')
                return redirect(url_for('bp_iwms.groups'))
    else:
        return render_template("auth/authorization_error.html")

@bp_iwms.route('/group_edit/<int:oid>',methods=['GET','POST'])
@login_required
def group_edit(oid):
    group = Group.query.get_or_404(oid)
    form = GroupEditForm(obj=group)
    if request.method == "GET":
        context['mm-active'] = 'Groups'
        return admin_edit(form,'bp_iwms.group_edit',oid,model=Group,template='iwms/iwms_edit.html',kwargs={'active':'system'})
    elif request.method == "POST":
        if form.validate_on_submit():
            group.name = form.name.data
            group.updated_at = datetime.now()
            group.updated_by = "{} {}".format(current_user.fname,current_user.lname)
            db.session.commit()
            flash('Group update Successfully!','success')
            _log_create("Group update","GroupID={}".format(group.id))
            return redirect(url_for('bp_iwms.groups'))
        else:    
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.groups'))


@bp_iwms.route('/emails')
@login_required
def emails():
    fields = [EAddress.id,EAddress.module_code,EAddress.description,EAddress.type,EAddress.email]
    form = EmailForm()
    context['mm-active'] = 'email'
    return admin_index(EAddress,fields=fields,form=form,url='', \
        create_url='bp_iwms.email_create',edit_url='bp_iwms.email_edit' \
            ,template="iwms/iwms_index.html",kwargs={'active':'system'})

@bp_iwms.route('/email_create',methods=['POST'])
@login_required
def email_create():
    if _check_create('email'):
        form = EmailForm()
        if request.method == 'POST':
            if form.validate_on_submit():
                email = EAddress()
                email.email = form.email.data
                email.module_code = form.module_code.data
                email.type = form.type.data
                email.description = form.description.data
                email.created_by = "{} {}".format(current_user.fname,current_user.lname)
                db.session.add(email)
                db.session.commit()
                flash('New Email address added successfully!','success')
                _log_create('New email address added','EmailAdressID={}'.format(email.id))
                return redirect(url_for('bp_iwms.emails'))
            else:
                for key, value in form.errors.items():
                    flash(str(key) + str(value), 'error')
                return redirect(url_for('bp_iwms.emails'))
    else:
        return render_template("auth/authorization_error.html")


@bp_iwms.route('/email_edit/<int:oid>',methods=['GET','POST'])
@login_required
def email_edit(oid):
    obj = EAddress.query.get_or_404(oid)
    f = EmailEditForm(obj=obj)

    if request.method == "GET":
        context['mm-active'] = 'email'

        return admin_edit(f,'bp_iwms.email_edit',oid,model=EAddress,template='iwms/iwms_edit.html',kwargs={'active':'system'})
    elif request.method == "POST":
        if f.validate_on_submit():
            obj.email = f.email.data
            obj.module_code = f.module_code.data
            obj.description = f.description.data
            obj.type = f.type.data
            obj.updated_at = datetime.now()
            obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
            db.session.commit()
            flash('Email address update Successfully!','success')
            _log_create('Email address update','EmailAdressID={}'.format(oid))
            return redirect(url_for('bp_iwms.emails'))
        else:    
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.emails'))

@bp_iwms.route('/departments')
@login_required
def departments():
    fields = [Department.id,Department.name]
    context['mm-active'] = 'department'
    return admin_index(Department,fields=fields,url='',form=DepartmentForm(), \
        template="iwms/iwms_index.html",kwargs={'active':'system'}, \
            create_url="bp_iwms.department_create",edit_url="bp_iwms.department_edit")

@bp_iwms.route('/department_create',methods=['POST'])
@login_required
def department_create():
    if _check_create('department'):
        form = DepartmentForm()
        if request.method == 'POST':
            if form.validate_on_submit():
                dept = Department()
                dept.name = form.name.data
                dept.created_by = "{} {}".format(current_user.fname,current_user.lname)
                db.session.add(dept)
                db.session.commit()
                flash('New department added successfully!','error')
                _log_create('New department added','DepartmentID={}'.format(dept.id))
                return redirect(url_for('bp_iwms.departments'))
            else:
                for key, value in form.errors.items():
                    flash(str(key) + str(value), 'error')
                return redirect(url_for('bp_iwms.departments'))
    else:
        return render_template("auth/authorization_error.html")

@bp_iwms.route('/department_edit/<int:oid>',methods=['GET','POST'])
@login_required
def department_edit(oid):
    obj = Department.query.get_or_404(oid)
    f = DepartmentEditForm(obj=obj)

    if request.method == "GET":
        context['mm-active'] = 'department'

        return admin_edit(f,'bp_iwms.department_edit',oid, \
            model=Department,template='iwms/iwms_edit.html',kwargs={'active':'system'})
    elif request.method == "POST":
        if f.validate_on_submit():
            obj.name = f.name.data
            obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
            obj.updated_at = datetime.now()
            db.session.commit()
            flash('Department update Successfully!','success')
            _log_create('Department update','DepartmentID={}'.format(oid))
            return redirect(url_for('bp_iwms.departments'))
        else:    
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.departments'))


@bp_iwms.route('/transaction_types')
@login_required
def transaction_types():
    fields = [TransactionType.id,TransactionType.code,TransactionType.description,TransactionType.prefix,TransactionType.next_number_series]
    context['mm-active'] = 'transaction_type'
    return admin_index(TransactionType,fields=fields,form=TransactionTypeForm(),template='iwms/iwms_index.html', \
        create_url='bp_iwms.transaction_type_create',edit_url="bp_iwms.transaction_type_edit",kwargs={'active':'system'})

@bp_iwms.route('/transaction_type_create',methods=["POST"])
@login_required
def transaction_type_create():
    if _check_create('transaction_type'):
        form = TransactionTypeForm()
        if request.method == 'POST':
            if form.validate_on_submit():
                tt = TransactionType()
                tt.next_number_series = form.next_number_series.data if not form.next_number_series.data == '' else 0
                tt.prefix = form.prefix.data
                tt.code = form.code.data
                tt.description = form.description.data
                tt.created_by = "{} {}".format(current_user.fname,current_user.lname)
                db.session.add(tt)
                db.session.commit()
                flash("New transaction type added successfully!",'success')
                _log_create("New transaction type added",'TransactionTypeID={}'.format(tt.id))
                return redirect(url_for('bp_iwms.transaction_types'))
            else:
                for key, value in form.errors.items():
                    flash(str(key) + str(value), 'error')
                return redirect(url_for('bp_iwms.transaction_types'))
    else:
        return render_template('auth/authorization_error.html')

@bp_iwms.route('/transaction_type_edit/<int:oid>',methods=['GET','POST'])
@login_required
def transaction_type_edit(oid):
    obj = TransactionType.query.get_or_404(oid)
    f = TransactionTypeEditForm(obj=obj)

    if request.method == "GET":
        context['mm-active'] = 'transaction_type'
        return admin_edit(f,'bp_iwms.transaction_type_edit',oid, \
            model=TransactionType,template='iwms/iwms_edit.html',kwargs={'active':'system'})
    elif request.method == "POST":
        if f.validate_on_submit():
            obj.code = f.code.data
            obj.description = f.description.data
            obj.prefix = f.prefix.data
            obj.next_number_series = f.next_number_series.data if not f.next_number_series.data == '' else None            
            obj.updated_at = datetime.now()
            obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
            db.session.commit()
            flash('Transaction type update Successfully!','success')
            _log_create("Transaction type update","TransactionTypeID={}".format(oid))
            return redirect(url_for('bp_iwms.transaction_types'))
        else:    
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.transaction_types'))

@bp_iwms.route('/logs')
@login_required
def logs():
    from app.auth.models import User
    fields = [CoreLog.id,User.fname,CoreLog.date,CoreLog.description,CoreLog.data]
    models = [CoreLog,User]
    context['mm-active'] = 'logs'
    return admin_index(*models,fields=fields,template='iwms/iwms_index.html',create_modal=False,view_modal=False,kwargs={
        'index_title':'System Logs','index_headers':['User','Date','Description','Data'],'index_message':'List of items',
        'active':'system'})

@bp_iwms.route('/warehouses')
@login_required
def warehouses():
    fields = [Warehouse.id,Warehouse.code,Warehouse.name,Warehouse.active,Warehouse.main_warehouse,Warehouse.updated_by,Warehouse.updated_at]
    context['mm-active'] = 'warehouse'
    return admin_index(Warehouse,fields=fields,form=WarehouseForm(),create_url='bp_iwms.warehouse_create',\
        edit_url='bp_iwms.warehouse_edit',template='iwms/iwms_index.html',kwargs={'active':'inventory','convert_boolean':2})

@bp_iwms.route('/warehouse_create',methods=['POST'])
@login_required
def warehouse_create():
    if _check_create('warehouse'):
        form = WarehouseForm()
        if request.method == "POST":
            if form.validate_on_submit():
                wh = Warehouse()
                wh.code = form.code.data
                wh.name = form.name.data
                wh.active = 1 if form.active.data == 'on' else 0
                wh.main_warehouse = 1 if form.main_warehouse.data == 'on' else 0
                wh.created_by = "{} {}".format(current_user.fname,current_user.lname)
                db.session.add(wh)
                db.session.commit()
                flash("New warehouse added successfully!",'success')
                return redirect(url_for('bp_iwms.warehouses'))
            else:
                for key, value in form.errors.items():
                    flash(str(key) + str(value), 'error')
                return redirect(url_for('bp_iwms.warehouses'))
    else:
        return render_template('auth/authorization_error.html')


@bp_iwms.route('/warehouse_edit/<int:oid>',methods=['GET','POST'])
@login_required
def warehouse_edit(oid):
    obj = Warehouse.query.get_or_404(oid)
    f = WarehouseEditForm(obj=obj)
    if request.method == "GET":
        context['mm-active'] = 'warehouse'
        return admin_edit(f,'bp_iwms.warehouse_edit',oid, \
            model=Warehouse,template='iwms/iwms_edit.html',kwargs={'active':'inventory'})
    elif request.method == "POST":
        if f.validate_on_submit():
            obj.code = f.code.data
            obj.name = f.name.data
            obj.active = 1 if f.active.data == 'on' else 0
            obj.main_warehouse = 1 if f.main_warehouse.data == 'on' else 0
            obj.updated_at = datetime.now()
            obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
            db.session.commit()
            flash('Warehouse update Successfully!','success')
            return redirect(url_for('bp_iwms.warehouses'))
        else:    
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.warehouses'))

@bp_iwms.route('/zones')
@login_required
def zones():
    fields = [Zone.id,Zone.code,Zone.description]
    context['mm-active'] = 'zone'
    return admin_index(Zone,fields=fields,form=ZoneForm(),create_url='bp_iwms.zone_create', \
        edit_url='bp_iwms.zone_edit',template='iwms/iwms_index.html',kwargs={'active':'inventory'})
    
@bp_iwms.route('/zone_create',methods=['POST'])
@login_required
def zone_create():
    if _check_create('zone'):
        f = ZoneForm()
        if request.method == "POST":
            if f.validate_on_submit():
                obj = Zone()
                obj.code = f.code.data
                obj.description = f.description.data
                obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
                db.session.add(obj)
                db.session.commit()
                flash("New zone added successfully!",'success')
                return redirect(url_for('bp_iwms.zones'))
            else:
                for key, value in f.errors.items():
                    flash(str(key) + str(value), 'error')
                return redirect(url_for('bp_iwms.zones'))
    else:
        return render_template('auth/authorization_error.html')

@bp_iwms.route('/zone_edit/<int:oid>',methods=['GET','POST'])
@login_required
def zone_edit(oid):
    obj = Zone.query.get_or_404(oid)
    f = ZoneEditForm(obj=obj)
    if request.method == "GET":
        context['mm-active'] = 'zone'

        return admin_edit(f,'bp_iwms.zone_edit',oid, \
            model=Warehouse,template='iwms/iwms_edit.html',kwargs={'active':'inventory'})
    elif request.method == "POST":
        if f.validate_on_submit():
            obj.code = f.code.data
            obj.description = f.description.data
            obj.updated_at = datetime.now()
            obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
            db.session.commit()
            flash('Zone update Successfully!','success')
            return redirect(url_for('bp_iwms.zones'))
        else:    
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.zones'))
    

@bp_iwms.route('/bin_locations')
@login_required
def bin_locations():
    fields = [
        BinLocation.id,BinLocation.index,BinLocation.code,BinLocation.description, \
            Warehouse.name,Zone.code,BinLocation.pallet_slot,BinLocation.pallet_cs, \
                BinLocation.capacity,BinLocation.weight_cap,BinLocation.cbm_cap
    ]
    models = [BinLocation,Warehouse,Zone]
    context['mm-active'] = 'bin_location'
    return admin_index(*models,fields=fields,form=BinLocationForm(), \
        template='iwms/iwms_index.html',create_url="bp_iwms.bin_location_create", \
            kwargs={'active':'inventory'},edit_url="bp_iwms.bin_location_edit")

@bp_iwms.route('/bin_location_create',methods=['POST'])
@login_required
def bin_location_create():
    if _check_create('bin_location'):
        f = BinLocationForm()
        if request.method == "POST":
            if f.validate_on_submit():
                obj = BinLocation()
                obj.code = f.code.data
                obj.description = f.description.data
                obj.index = f.index.data if not f.index.data == '' else 0
                obj.warehouse_id = f.warehouse_id.data if not f.warehouse_id.data == '' else None
                obj.zone_id = f.zone_id.data if not f.zone_id.data == '' else None
                obj.pallet_slot = f.pallet_slot.data if not f.pallet_slot.data == '' else 0
                obj.pallet_cs = f.pallet_cs.data if not f.pallet_cs.data == '' else 0
                obj.capacity = f.capacity.data if not f.capacity.data == '' else 0
                obj.weight_cap = f.weight_cap.data if not f.weight_cap.data == '' else 0
                obj.cbm_cap = f.cbm_cap.data if not f.cbm_cap.data == '' else 0
                obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
                db.session.add(obj)
                db.session.commit()
                flash("New Bin Location added successfully!",'success')
                return redirect(url_for('bp_iwms.bin_locations'))
            else:
                for key, value in f.errors.items():
                    flash(str(key) + str(value), 'error')
                return redirect(url_for('bp_iwms.bin_locations'))
    else:
        return render_template('auth/authorization_error.html')

@bp_iwms.route('/bin_location_edit/<int:oid>',methods=['GET','POST'])
@login_required
def bin_location_edit(oid):
    obj = BinLocation.query.get_or_404(oid)
    f = BinLocationEditForm(obj=obj)
    if request.method == "GET":
        context['mm-active'] = 'bin_location'

        return admin_edit(f,'bp_iwms.bin_location_edit',oid, \
            model=BinLocation,template='iwms/iwms_edit.html',kwargs={'active':'inventory'})
    elif request.method == "POST":
        if f.validate_on_submit():
            obj.code = f.code.data
            obj.description = f.description.data
            obj.index = f.index.data if not f.index.data == '' else 0
            obj.warehouse_id = f.warehouse_id.data if not f.warehouse_id.data == '' else None
            obj.zone_id = f.zone_id.data if not f.zone_id.data == '' else None
            obj.pallet_slot = f.pallet_slot.data if not f.pallet_slot.data == '' else 0
            obj.pallet_cs = f.pallet_cs.data if not f.pallet_cs.data == '' else 0
            obj.capacity = f.capacity.data if not f.capacity.data == '' else 0
            obj.weight_cap = f.weight_cap.data if not f.weight_cap.data == '' else 0
            obj.cbm_cap = f.cbm_cap.data if not f.cbm_cap.data == '' else 0
            obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
            obj.updated_at = datetime.now()
            db.session.commit()
            flash('Bin Location update Successfully!','success')
            return redirect(url_for('bp_iwms.bin_locations'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.bin_locations'))

@bp_iwms.route('/categories')
@login_required
def categories():
    fields = [Category.id,Category.code,Category.description]
    context['mm-active'] = 'category'
    return admin_index(Category,fields=fields,form=CategoryForm(), \
        template='iwms/iwms_index.html',create_url="bp_iwms.category_create", \
            edit_url='bp_iwms.category_edit',kwargs={'active':'inventory'})

@bp_iwms.route('/category_create',methods=['POST'])
@login_required
def category_create():
    f = CategoryForm()
    if request.method == "POST":
        if f.validate_on_submit():
            obj = Category()
            obj.code = f.code.data
            obj.description = f.description.data
            obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
            db.session.add(obj)
            db.session.commit()
            flash("New Category added successfully!",'success')
            return redirect(url_for('bp_iwms.categories'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.categories'))

@bp_iwms.route('/category_edit/<int:oid>',methods=['GET','POST'])
@login_required
def category_edit(oid):
    obj = Category.query.get_or_404(oid)
    f = CategoryEditForm(obj=obj)
    if request.method == "GET":
        context['mm-active'] = 'category'

        return admin_edit(f,'bp_iwms.category_edit',oid, \
            model=Category,template='iwms/iwms_edit.html',kwargs={'active':'inventory'})
    elif request.method == "POST":
        if f.validate_on_submit():
            obj.code = f.code.data
            obj.description = f.description.data
            obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
            obj.updated_at = datetime.now()
            db.session.commit()
            flash('Category update Successfully!','success')
            return redirect(url_for('bp_iwms.categories'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.categories'))

@bp_iwms.route('/unit_of_measures')
@login_required
def unit_of_measures():
    fields = [UnitOfMeasure.id,UnitOfMeasure.code,UnitOfMeasure.description,UnitOfMeasure.active]
    context['mm-active'] = 'unit_of_measure'
    return admin_index(UnitOfMeasure,fields=fields,form=UnitOfMeasureForm(), \
        template='iwms/iwms_index.html', edit_url='bp_iwms.unit_of_measure_edit', \
            create_url="bp_iwms.unit_of_measure_create",kwargs={'active':'inventory'})

@bp_iwms.route('/unit_of_measure_create',methods=['POST'])
@login_required
def unit_of_measure_create():
    f = UnitOfMeasureForm()
    if request.method == "POST":
        if f.validate_on_submit():
            obj = UnitOfMeasure()
            obj.code = f.code.data
            obj.description = f.description.data
            obj.active = 1 if f.active.data == 'on' else 0
            obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
            db.session.add(obj)
            db.session.commit()
            flash("New Unit of measure added successfully!",'success')
            return redirect(url_for('bp_iwms.unit_of_measures'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.unit_of_measures'))


@bp_iwms.route('/unit_of_measure_edit/<int:oid>',methods=['GET','POST'])
@login_required
def unit_of_measure_edit(oid):
    obj = UnitOfMeasure.query.get_or_404(oid)
    f = UnitOfMeasureEditForm(obj=obj)
    if request.method == "GET":
        context['mm-active'] = 'unit_of_measure'

        return admin_edit(f,'bp_iwms.unit_of_measure_edit',oid, \
            model=UnitOfMeasure,template='iwms/iwms_edit.html',kwargs={'active':'inventory'})
    elif request.method == "POST":
        if f.validate_on_submit():
            obj.code = f.code.data
            obj.description = f.description.data
            obj.active = 1 if f.active.data == 'on' else 0
            obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
            obj.updated_at = datetime.now()
            db.session.commit()
            flash('Unit of measure update Successfully!','success')
            return redirect(url_for('bp_iwms.unit_of_measures'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.unit_of_measures'))

@bp_iwms.route('/reasons')
@login_required
def reasons():
    fields = [Reason.id,Reason.code,Reason.type,Reason.description]
    context['mm-active'] = 'reason'
    return admin_index(Reason,fields=fields,form=ReasonForm(), \
        template='iwms/iwms_index.html', edit_url='bp_iwms.reason_edit',\
            create_url="bp_iwms.reason_create",kwargs={'active':'inventory'})

@bp_iwms.route('/reason_create',methods=['POST'])
@login_required
def reason_create():
    f = ReasonForm()
    if request.method == "POST":
        if f.validate_on_submit():
            obj = Reason()
            obj.code = f.code.data
            obj.description = f.description.data
            obj.type = f.type.data
            obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
            db.session.add(obj)
            db.session.commit()
            flash("New reason added successfully!",'success')
            return redirect(url_for('bp_iwms.reasons'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.reasons'))

@bp_iwms.route('/reason_edit/<int:oid>',methods=['GET','POST'])
@login_required
def reason_edit(oid):
    obj = Reason.query.get_or_404(oid)
    f = ReasonEditForm(obj=obj)
    if request.method == "GET":
        context['mm-active'] = 'reason'

        return admin_edit(f,'bp_iwms.reason_edit',oid, \
            model=Reason,template='iwms/iwms_edit.html',kwargs={'active':'inventory'})
    elif request.method == "POST":
        if f.validate_on_submit():
            obj.code = f.code.data
            obj.description = f.description.data
            obj.type = f.type.data
            obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
            obj.updated_at = datetime.now()
            db.session.commit()
            flash('Reason update Successfully!','success')
            return redirect(url_for('bp_iwms.reasons'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.reasons'))


@bp_iwms.route('/sources')
@login_required
def sources():
    fields = [Source.id,Source.name,Source.description]
    context['mm-active'] = 'source'
    return admin_index(Source,fields=fields,form=SourceForm(), \
        template='iwms/iwms_index.html', edit_url='bp_iwms.source_edit',\
            create_url="bp_iwms.source_create",kwargs={'active':'inventory'})

@bp_iwms.route('/source_create',methods=['POST'])
@login_required
def source_create():
    f = SourceForm()
    if request.method == "POST":
        if f.validate_on_submit():
            obj = Source()
            obj.name = f.name.data
            obj.description = f.description.data
            obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
            db.session.add(obj)
            db.session.commit()
            flash("New source added successfully!",'success')
            return redirect(url_for('bp_iwms.sources'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.sources'))

@bp_iwms.route('/source_edit/<int:oid>',methods=['GET','POST'])
@login_required
def source_edit(oid):
    obj = Source.query.get_or_404(oid)
    f = SourceEditForm(obj=obj)
    if request.method == "GET":
        context['mm-active'] = 'source'
        return admin_edit(f,'bp_iwms.source_edit',oid, \
            model=Source,template='iwms/iwms_edit.html',kwargs={'active':'inventory'})
    elif request.method == "POST":
        if f.validate_on_submit():
            obj.name = f.name.data
            obj.description = f.description.data
            obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
            obj.updated_at = datetime.now()
            db.session.commit()
            flash('Source update Successfully!','success')
            return redirect(url_for('bp_iwms.sources'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.sources'))


@bp_iwms.route('/stock_items')
@login_required
def stock_items():
    fields = [StockItem.id,StockItem.number,StockItem.name,StockItem.description]
    context['mm-active'] = 'stock_item'
    # TODO: Kailangan idelete yung context['create_modal'] kasi naiiwan sya
    form = StockItemView()
    context['create_modal']['create_url'] = False
    return admin_index(StockItem,form=form,fields=fields,edit_url="bp_iwms.stock_item_edit",create_modal=True,template="iwms/iwms_index.html",kwargs={
        'active':'inventory'
        })

@bp_iwms.route('/stock_item_create',methods=['GET','POST'])
@login_required
def stock_item_create():
    si_generated_number = ""
    si = db.session.query(StockItem).order_by(StockItem.id.desc()).first()
    if si:
        si_generated_number = _generate_number("SI",si.id)
    else:
        # MAY issue to kasi kapag hindi na truncate yung table magkaiba na yung id at number ng po
        # Make sure nakatruncate ang mga table ng po para reset yung auto increment na id
        si_generated_number = "SI00000001"

    f = StockItemCreateForm()

    if request.method == "GET":
        categories = Category.query.all()
        types = StockItemType.query.all()
        suppliers = Supplier.query.all()
        tax_codes = TaxCode.query.all()
        uoms = UnitOfMeasure.query.all()
        context['active'] = 'inventory'
        context['module'] = 'iwms'
        context['model'] = 'stock_item'
        context['mm-active'] = 'stock_item'

        # Hardcoded html ang irerender natin hindi yung builtin ng admin
        return render_template('iwms/stock_item/iwms_stock_item_create.html',context=context,si_generated_number=si_generated_number,\
            form=f,categories=categories,types=types,title="Create stock item",suppliers=suppliers,tax_codes=tax_codes,\
                uoms=uoms)
    elif request.method == "POST":
        if f.validate_on_submit():
            obj = StockItem()
            obj.number = si_generated_number
            obj.status = "active"
            obj.stock_item_type_id = f.stock_item_type_id.data if not f.stock_item_type_id.data == '' else None 
            obj.category_id = f.category_id.data if not f.category_id.data == '' else None
            obj.has_serial = 1 if f.has_serial.data == 'on' else 0
            obj.monitor_expiration = 1 if f.monitor_expiration.data == 'on' else 0
            obj.brand = f.brand.data
            obj.name = f.name.data
            obj.description = f.description.data
            obj.cap_size,obj.cap_profile,obj.compound,obj.clients = None, None, None, None
            obj.packaging = f.packaging.data
            obj.tax_code_id = f.tax_code_id.data if not f.tax_code_id.data == '' else None
            obj.reorder_qty = f.reorder_qty.data if not f.reorder_qty.data == '' else None
            obj.description_plu = f.description_plu.data
            obj.barcode = f.barcode.data if not f.barcode.data == '' else None
            obj.qty_plu = f.qty_plu.data if not f.qty_plu.data == '' else None
            obj.length = f.length.data
            obj.width = f.width.data
            obj.height = f.height.data
            obj.unit_id = f.unit_id.data if not f.unit_id.data == '' else None
            obj.default_cost = f.default_cost.data if not f.default_cost.data == '' else None
            obj.default_price = f.default_price.data if not f.default_price.data == '' else None
            obj.weight = f.weight.data
            obj.cbm = f.cbm.data
            obj.qty_per_pallet = f.qty_per_pallet.data if not f.qty_per_pallet.data == '' else None
            obj.shelf_life = f.shelf_life.data if not f.shelf_life.data == '' else None
            obj.qa_lead_time = f.qa_lead_time.data if not f.qa_lead_time.data == '' else None
            obj.created_by = "{} {}".format(current_user.fname,current_user.lname)

            supplier_ids = request.form.getlist('suppliers')
            if supplier_ids:
                for s_id in supplier_ids:
                    supplier = Supplier.query.get_or_404(int(s_id))
                    obj.suppliers.append(supplier)

            uom_ids = request.form.getlist('uoms[]')
            if uom_ids:
                for u_id in uom_ids:
                    uom = UnitOfMeasure.query.get(u_id)
                    qty = request.form.get("qty_{}".format(u_id))
                    barcode = request.form.get("barcode_{}".format(u_id))
                    _cost = request.form.get("default_cost_{}".format(u_id))
                    _price = request.form.get("default_price_{}".format(u_id))
                    default_cost = _cost if not _cost == '' else None
                    default_price = _price if not _price == '' else None
                    length = request.form.get("length_{}".format(u_id))
                    width = request.form.get("width_{}".format(u_id))
                    height = request.form.get("height_{}".format(u_id))
                    line = StockItemUomLine(uom=uom,qty=qty,barcode=barcode,default_cost=default_cost,default_price=default_price,\
                        length=length,width=width,height=height)
                    obj.uom_line.append(line)

            db.session.add(obj)
            db.session.commit()
            flash('New Stock Item added Successfully!','success')
            return redirect(url_for('bp_iwms.stock_items'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.stock_items'))

@bp_iwms.route('/stock_item_edit/<int:oid>',methods=['GET','POST'])
@login_required
def stock_item_edit(oid):
    obj = StockItem.query.get_or_404(oid)
    f = StockItemCreateForm(obj=obj)
    if request.method == "GET":
        context['active'] = 'inventory'
        context['module'] = 'iwms'
        context['model'] = 'stock_item'
        context['mm-active'] = 'stock_item'
        
        categories = Category.query.all()
        types = StockItemType.query.all()
        suppliers = Supplier.query.all()
        tax_codes = TaxCode.query.all()
        units = UnitOfMeasure.query.all()

        selected_suppliers = []
        for selected in obj.suppliers:
            selected_suppliers.append(selected.id)

        query1 = db.session.query(StockItemUomLine.uom_id).filter_by(stock_item_id=oid)
        uoms = db.session.query(UnitOfMeasure).filter(~UnitOfMeasure.id.in_(query1))
        return render_template('iwms/stock_item/iwms_stock_item_edit.html',context=context,form=f,types=types, uom_lines=obj.uom_line,\
            categories=categories,selected_suppliers=selected_suppliers,suppliers=suppliers,uoms=uoms,units=units,title="Edit stock item",\
                oid=oid)
    elif request.method == "POST":
        if f.validate_on_submit():
            obj.status = "active"
            obj.stock_item_type_id = f.stock_item_type_id.data if not f.stock_item_type_id.data == '' else None 
            obj.category_id = f.category_id.data if not f.category_id.data == '' else None
            obj.has_serial = 1 if f.has_serial.data == 'on' else 0
            obj.monitor_expiration = 1 if f.monitor_expiration.data == 'on' else 0
            obj.brand = f.brand.data
            obj.name = f.name.data
            obj.description = f.description.data
            obj.cap_size,obj.cap_profile,obj.compound,obj.clients = None, None, None, None
            obj.packaging = f.packaging.data
            obj.tax_code_id = f.tax_code_id.data if not f.tax_code_id.data == '' else None
            obj.reorder_qty = f.reorder_qty.data if not f.reorder_qty.data == '' else None
            obj.description_plu = f.description_plu.data
            obj.barcode = f.barcode.data if not f.barcode.data == '' else None
            obj.qty_plu = f.qty_plu.data if not f.qty_plu.data == '' else None
            obj.length = f.length.data
            obj.width = f.width.data
            obj.height = f.height.data
            obj.unit_id = f.unit_id.data if not f.unit_id.data == '' else None
            obj.default_cost = f.default_cost.data if not f.default_cost.data == '' else None
            obj.default_price = f.default_price.data if not f.default_price.data == '' else None
            obj.weight = f.weight.data
            obj.cbm = f.cbm.data
            obj.qty_per_pallet = f.qty_per_pallet.data if not f.qty_per_pallet.data == '' else None
            obj.shelf_life = f.shelf_life.data if not f.shelf_life.data == '' else None
            obj.qa_lead_time = f.qa_lead_time.data if not f.qa_lead_time.data == '' else None
            obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
            obj.updated_at = datetime.now()

            supplier_ids = request.form.getlist('suppliers')
            if supplier_ids:
                obj.suppliers = []
                for new_sup in supplier_ids:
                    supp = Supplier.query.get_or_404(new_sup)
                    obj.suppliers.append(supp)

            uom_ids = request.form.getlist('uoms[]')
            if uom_ids:
                obj.uom_line = []
                for u_id in uom_ids:
                    uom = UnitOfMeasure.query.get(u_id)
                    qty = request.form.get("qty_{}".format(u_id))
                    barcode = request.form.get("barcode_{}".format(u_id))
                    default_cost = request.form.get("default_cost_{}".format(u_id))
                    default_price = request.form.get("default_price_{}".format(u_id))
                    length = request.form.get("length_{}".format(u_id))
                    width = request.form.get("width_{}".format(u_id))
                    height = request.form.get("height_{}".format(u_id))
                    line = StockItemUomLine(uom=uom,qty=qty,barcode=barcode,default_cost=default_cost,default_price=default_price,\
                        length=length,width=width,height=height)
                    obj.uom_line.append(line)
                    
            db.session.commit()
            flash('Stock Item updated Successfully!','success')
            return redirect(url_for('bp_iwms.stock_items'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.stock_items'))


@bp_iwms.route('/stock_receipts')
@login_required
def stock_receipts():
    fields = [StockReceipt.id,StockReceipt.sr_number,StockReceipt.created_at,StockReceipt.created_by,StockReceipt.status]
    # Custom models pass to admin_index
    models = StockReceipt.query.with_entities(*fields).filter_by(status="LOGGED").all()
    context['mm-active'] = 'stock_receipt'
    context['create_modal']['create_url'] = False
    return admin_index(StockReceipt,fields=fields,form=StockReceiptViewForm(),create_modal=True,template="iwms/iwms_index.html",\
        kwargs={'active':'inventory','models': models})

@bp_iwms.route('/stock_receipt_create',methods=['GET','POST'])
@login_required
def stock_receipt_create():
    sr_generated_number = ""
    sr = db.session.query(StockReceipt).order_by(StockReceipt.id.desc()).first()
    if sr:
        sr_generated_number = _generate_number("SR",sr.id)
    else:
        # MAY issue to kasi kapag hindi na truncate yung table magkaiba na yung id at number ng po
        # Make sure nakatruncate ang mga table ng po para reset yung auto increment na id
        sr_generated_number = "SR00000001"
    
    f = StockReceiptCreateForm()
    if request.method == "GET":
        # Hardcoded html ang irerender natin hindi yung builtin ng admin
        warehouses = Warehouse.query.all()
        po_list = PurchaseOrder.query.filter_by(status="LOGGED")
        sources = Source.query.all()
        context['active'] = 'inventory'
        context['mm-active'] = 'stock_receipt'
        context['module'] = 'iwms'
        context['model'] = 'stock_receipt'
        return render_template('iwms/stock_receipt/iwms_stock_receipt_create.html',context=context,po_list=po_list,sources=sources,\
            form=f,title="Create stock receipt",warehouses=warehouses,sr_generated_number=sr_generated_number)
    elif request.method == "POST":
        if f.validate_on_submit():
            obj = StockReceipt()
            obj.sr_number = sr_generated_number
            # No field yet so hardcoded muna
            po = PurchaseOrder.query.filter_by(po_number=f.po_number.data).first()
            po.status = "RELEASED"
            obj.purchase_order = po
            obj.status = "LOGGED"
            obj.warehouse_id = po.warehouse_id
            obj.source_id = f.source.data if not f.source.data == '' else None
            obj.po_number = f.po_number.data
            obj.supplier = f.supplier.data
            obj.reference = f.reference.data
            obj.si_number = f.si_number.data
            obj.bol = f.bol.data
            obj.remarks = f.remarks.data
            obj.date_received = f.date_received.data
            obj.putaway_txn = f.putaway_txn.data
            obj.created_by = "{} {}".format(current_user.fname,current_user.lname)

            item_list = request.form.getlist('sr_items[]')
            if item_list:
                for item_id in item_list:
                    item = StockItem.query.get(item_id)
                    lot_no = request.form.get("lot_no_{}".format(item_id))
                    expiry_date = request.form.get("expiry_date_{}".format(item_id)) if not request.form.get("expiry_date_{}".format(item_id)) == '' else None
                    uom = request.form.get("uom_{}".format(item_id))
                    received_qty = request.form.get("received_qty_{}".format(item_id)) if not request.form.get("received_qty_{}".format(item_id)) == '' else None
                    net_weight = request.form.get("net_weight_{}".format(item_id)) if not request.form.get("net_weight_{}".format(item_id)) == '' else None
                    # timestamp = r.get("timestamp_{}".format(item_id))
                    line = StockReceiptItemLine(stock_item=item,lot_no=lot_no,expiry_date=expiry_date,\
                        uom=uom,received_qty=received_qty,net_weight=net_weight)
                    obj.item_line.append(line)

            db.session.add(obj)
            db.session.commit()
            flash('New Stock Receipt added Successfully!','success')
            return redirect(url_for('bp_iwms.stock_receipts'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.stock_receipts'))
        
@bp_iwms.route('/putaways')
@login_required
def putaways():
    fields = [Putaway.id,Putaway.pwy_number,Putaway.created_at,Putaway.created_by,Putaway.status]
    context['mm-active'] = 'putaway' 
    context['create_modal']['create_url'] = False
    return admin_index(Putaway,fields=fields,form=PutawayViewForm(),create_modal=True,template="iwms/iwms_index.html",kwargs={'active':'inventory'})

@bp_iwms.route('/putaway_create',methods=['GET','POST'])
@login_required
def putaway_create():
    pwy_generated_number = ""
    pwy = db.session.query(Putaway).order_by(Putaway.id.desc()).first()
    if pwy:
        pwy_generated_number = _generate_number("PWY",pwy.id)
    else:
        # MAY issue to kasi kapag hindi na truncate yung table magkaiba na yung id at number ng po
        # Make sure nakatruncate ang mga table ng po para reset yung auto increment na id
        pwy_generated_number = "PWY00000001"

    f = PutawayCreateForm()
    if request.method == "GET":
        # Hardcoded html ang irerender natin hindi yung builtin ng admin
        warehouses = Warehouse.query.all()
        sr_list = StockReceipt.query.filter_by(status="LOGGED")
        bin_locations = BinLocation.query.all()
        context['active'] = 'inventory'
        context['mm-active'] = 'putaway'
        context['module'] = 'iwms'
        context['model'] = 'putaway'
        return render_template('iwms/putaway/iwms_putaway_create.html',context=context,form=f,title="Create putaway",\
            warehouses=warehouses,pwy_generated_number=pwy_generated_number,sr_list=sr_list,bin_locations=bin_locations)
    elif request.method == "POST":
        if f.validate_on_submit():
            obj = Putaway()
            sr = StockReceipt.query.filter_by(sr_number=f.sr_number.data).first()
            obj.stock_receipt = sr
            obj.pwy_number = pwy_generated_number
            obj.status = "LOGGED"
            sr.status = "COMPLETED"
            sr.purchase_order.status = "COMPLETED"
            # obj.warehouse_id = 
            obj.reference = f.reference.data
            obj.remarks = f.remarks.data
            obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
            items_list = request.form.getlist('pwy_items[]')
            if items_list:
                for item_id in items_list:
                    item = StockItem.query.get(item_id)
                    lot_no = request.form.get('lot_no_{}'.format(item_id))
                    expiry_date = request.form.get('expiry_{}'.format(item_id)) if not request.form.get('expiry_{}'.format(item_id)) == '' else None
                    uom = request.form.get('uom_{}'.format(item_id))
                    qty = request.form.get('qty_{}'.format(item_id)) if not request.form.get('qty_{}'.format(item_id)) == '' else None
                    line = PutawayItemLine(stock_item=item,lot_no=lot_no,expiry_date=expiry_date,uom=uom,qty=qty)
                    obj.item_line.append(line)

            db.session.add(obj)
            db.session.commit()
            flash('New Putaway added Successfully!','success')
            return redirect(url_for('bp_iwms.putaways'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.putaways'))

@bp_iwms.route("/_get_suppliers",methods=['POST'])
def _get_suppliers():
    if request.method == 'POST':
        sup_id = request.json['sup_id']
        db_items = StockItem.query.filter(StockItem.suppliers.any(id=sup_id)).all()
        list_items = []
        for item in db_items:
            list_items.append({'id':item.id,'number':item.number,'name':item.name,'description':item.description,'barcode':item.barcode,'default_cost':str(item.default_cost)})
        res = jsonify(items=list_items)
        res.status_code = 200
        return res

@bp_iwms.route('/purchase_orders')
@login_required
def purchase_orders():
    fields = [PurchaseOrder.id,PurchaseOrder.po_number,PurchaseOrder.created_at,PurchaseOrder.created_by,PurchaseOrder.status.name]
    context['mm-active'] = 'purchase_order'
    # TEMPORARY LANG TO, may bug kasi
    context['create_modal']['create_url'] = False
    return admin_index(PurchaseOrder,fields=fields,form=PurchaseOrderViewForm(),create_modal=True,template="iwms/iwms_index.html",kwargs={
        'active':'purchases'},edit_url="bp_iwms.purchase_order_edit")

@bp_iwms.route('/purchase_order_create',methods=['GET','POST'])
@login_required
def purchase_order_create():
    import platform

    po_generated_number = ""
    po = db.session.query(PurchaseOrder).order_by(PurchaseOrder.id.desc()).first()
    if po:
        po_generated_number = _generate_number("PO",po.id)
    else:
        # MAY issue to kasi kapag hindi na truncate yung table magkaiba na yung id at number ng po
        # Make sure nakatruncate ang mga table ng po para reset yung auto increment na id
        po_generated_number = "PO00000001"
    
    f = PurchaseOrderCreateForm()
    if request.method == "GET":
        warehouses = Warehouse.query.all()
        suppliers = Supplier.query.all()
        # stock_items = StockItem.query.all()
        # Hardcoded html ang irerender natin hindi yung builtin ng admin
        context['active'] = 'purchases'
        context['mm-active'] = 'purchase_order'
        context['module'] = 'iwms'
        context['model'] = 'purchase_order'
        return render_template('iwms/purchase_order/iwms_purchase_order_create.html', po_generated_number=po_generated_number, \
            context=context,form=f,title="Create purchase order",warehouses=warehouses,suppliers=suppliers)
    elif request.method == "POST":
        if f.validate_on_submit():
            r = request.form
            po = PurchaseOrder()
            po.po_number = po_generated_number
            po.supplier_id = f.supplier_id.data if not f.supplier_id.data == '' else None
            po.warehouse_id = f.warehouse_id.data if not f.warehouse_id.data == '' else None
            po.ship_to = f.ship_to.data
            po.address = f.address.data
            po.remarks = f.remarks.data
            po.ordered_date = f.ordered_date.data if not f.ordered_date.data == '' else None
            po.delivery_date = f.delivery_date.data if not f.delivery_date.data == '' else None
            po.approved_by = f.approved_by.data
            po.created_by = "{} {}".format(current_user.fname,current_user.lname)

            product_list = r.getlist('products[]')
            if product_list:
                for product_id in r.getlist('products[]'):
                    product = StockItem.query.get(product_id)
                    qty = r.get("qty_{}".format(product_id))
                    cost = r.get("cost_{}".format(product_id))
                    amount = r.get("amount_{}".format(product_id))
                    uom = UnitOfMeasure.query.get(r.get("uom_{}".format(product_id)))
                    line = PurchaseOrderProductLine(stock_item=product,qty=qty,unit_cost=cost,amount=amount,uom=uom)
                    po.product_line.append(line)
            db.session.add(po)
            db.session.commit()

            if request.form['btn_submit'] == 'Save and Print':
                file_name = po_generated_number + '.pdf'
                file_path = current_app.config['PDF_FOLDER'] + po_generated_number + '.pdf'
                
                """ CONVERT HTML STRING TO PDF THEN RETURN PDF TO BROWSER TO PRINT
                """
                if platform.system() == "Windows":
                    path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe' # CHANGE THIS to the location of wkhtmltopdf
                    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
                    pdfkit.from_string(_makePOPDF(po.supplier,po.product_line),file_path,configuration=config)
                else:
                    pdfkit.from_string(_makePOPDF(po.supplier,po.product_line),file_path)

                """ SEND EMAIL TO SUPPLIER'S EMAIL ADDRESS AND ATTACHED THE SAVED PDF IN /STATIC/PDFS FOLDER
                """
                
                msg = Message('Purchase Order', sender = 'rmontemayor0101@gmail.com', recipients = [po.supplier.email_address])
                msg.body = "Here attached purchase order quotation"

                with open(file_path,'rb') as pdf_file:
                    msg.attach(filename=file_path,disposition="attachment",content_type="application/pdf",data=pdf_file.read())
                mail.send(msg)
                flash('New Purchase Order added Successfully!','success')
                return send_from_directory(directory=current_app.config['PDF_FOLDER'],filename=file_name,as_attachment=True)
            else:
                flash('New Purchase Order added Successfully!','success')
                return redirect(url_for('bp_iwms.purchase_orders'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.purchase_orders'))

@bp_iwms.route('/purchase_order_edit/<int:oid>',methods=['GET','POST'])
@login_required
def purchase_order_edit(oid):
    po = PurchaseOrder.query.get_or_404(oid)
    f = PurchaseOrderCreateForm(obj=po)
    if request.method == "GET":
        warehouses = Warehouse.query.all()
        suppliers = Supplier.query.all()
        # stock_items = StockItem.query.all()
        # Hardcoded html ang irerender natin hindi yung builtin ng admin
        context['active'] = 'purchases'
        context['mm-active'] = 'purchase_order'
        context['module'] = 'iwms'
        context['model'] = 'purchase_order'

        # query1 = db.session.query(StockItemUomLine.uom_id).filter_by(stock_item_id=oid)
        # stock_items = db.session.query(UnitOfMeasure).filter(~UnitOfMeasure.id.in_(query1))

        return render_template('iwms/purchase_order/iwms_purchase_order_edit.html', oid=oid,stock_items='',line_items=po.product_line, \
            context=context,form=f,title="Edit purchase order",warehouses=warehouses,suppliers=suppliers)
    elif request.method == "POST":
        if f.validate_on_submit():
            po.supplier_id = f.supplier_id.data if not f.supplier_id.data == '' else None
            po.warehouse_id = f.warehouse_id.data if not f.warehouse_id.data == '' else None
            po.ship_to = f.ship_to.data
            po.address = f.address.data
            po.remarks = f.remarks.data
            po.ordered_date = f.ordered_date.data if not f.ordered_date.data == '' else None
            po.delivery_date = f.delivery_date.data if not f.delivery_date.data == '' else None
            po.approved_by = f.approved_by.data
            po.updated_by = "{} {}".format(current_user.fname,current_user.lname)

            product_list = request.form.getlist('products[]')
            if product_list:
                po.product_line = []
                for product_id in product_list:
                    product = StockItem.query.get(product_id)
                    qty = request.form.get("qty_{}".format(product_id))
                    cost = request.form.get("cost_{}".format(product_id))
                    amount = request.form.get("amount_{}".format(product_id))
                    uom = UnitOfMeasure.query.get(request.form.get("uom_{}".format(product_id)))
                    line = PurchaseOrderProductLine(stock_item=product,qty=qty,unit_cost=cost,amount=amount,uom=uom)
                    po.product_line.append(line)

            db.session.commit()

            if request.form['btn_submit'] == 'Save and Print':
                file_name = po.po_number + '.pdf'
                file_path = current_app.config['PDF_FOLDER'] + po.po_number + '.pdf'
                """ CONVERT HTML STRING TO PDF THEN RETURN PDF TO BROWSER TO PRINT
                """
                if platform.system() == "Windows":
                    path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe' # CHANGE THIS to the location of wkhtmltopdf
                    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
                    pdfkit.from_string(_makePOPDF(po.supplier,po.product_line),file_path,configuration=config)
                else:
                    pdfkit.from_string(_makePOPDF(po.supplier,po.product_line),file_path)
                    
                flash('Purchase Order updated Successfully!','success')
                return send_from_directory(directory=current_app.config['PDF_FOLDER'],filename=file_name,as_attachment=True)

            flash('Purchase Order updated Successfully!','success')
            return redirect(url_for('bp_iwms.purchase_orders'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.purchase_orders'))


@bp_iwms.route('/suppliers')
@login_required
def suppliers():
    fields = [Supplier.id,Supplier.code,Supplier.name,Supplier.status]
    context['mm-active'] = 'supplier'
    form = SupplierForm()
    sup_generated_number = ""
    sup = db.session.query(Supplier).order_by(Supplier.id.desc()).first()
    if sup:
        sup_generated_number = _generate_number("SUP",sup.id)
    else:
        # MAY issue to kasi kapag hindi na truncate yung table magkaiba na yung id at number ng po
        # Make sure nakatruncate ang mga table ng po para reset yung auto increment na id
        sup_generated_number = "SUP00000001"
    form.code.auto_generated = sup_generated_number
    return admin_index(Supplier,fields=fields,form=form, \
        template='iwms/iwms_index.html', edit_url='bp_iwms.supplier_edit',\
            create_url="bp_iwms.supplier_create",kwargs={'active':'purchases'})

@bp_iwms.route('/supplier_create',methods=['POST'])
@login_required
def supplier_create():
    f = SupplierForm()
    if request.method == "POST":
        if f.validate_on_submit():
            obj = Supplier()
            obj.code = f.code.data
            obj.name = f.name.data
            obj.status = "ACTIVE"
            obj.address = f.address.data
            obj.email_address = f.email_address.data
            obj.contact_person = f.contact_person.data
            obj.contact_number = f.contact_number.data
            obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
            db.session.add(obj)
            db.session.commit()
            flash("New supplier added successfully!",'success')
            return redirect(url_for('bp_iwms.suppliers'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.suppliers'))

@bp_iwms.route('/supplier_edit/<int:oid>',methods=['GET','POST'])
@login_required
def supplier_edit(oid):
    obj = Supplier.query.get_or_404(oid)
    f = SupplierEditForm(obj=obj)
    if request.method == "GET":
        context['mm-active'] = 'supplier'

        return admin_edit(f,'bp_iwms.supplier_edit',oid, \
            model=Supplier,template='iwms/iwms_edit.html',kwargs={'active':'purchases'})
    elif request.method == "POST":
        if f.validate_on_submit():
            obj.code = f.code.data
            obj.name = f.name.data
            obj.status = "ACTIVE"
            obj.address = f.address.data
            obj.email_address = f.email_address.data
            obj.contact_person = f.contact_person.data
            obj.contact_number = f.contact_number.data
            obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
            obj.updated_at = datetime.now()
            db.session.commit()
            flash('Supplier update Successfully!','success')
            return redirect(url_for('bp_iwms.suppliers'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.suppliers'))


@bp_iwms.route('/stock_item_types')
@login_required
def stock_item_types():
    fields = [StockItemType.id,StockItemType.name,StockItemType.created_by,StockItemType.created_at]
    context['mm-active'] = 'stock_item_type'
    return admin_index(StockItemType,fields=fields,form=TypeForm(), \
        template='iwms/iwms_index.html', edit_url='bp_iwms.type_edit',\
            create_url="bp_iwms.type_create",kwargs={'active':'inventory'})

@bp_iwms.route('/type_create',methods=['POST'])
@login_required
def type_create():
    f = TypeForm()
    if request.method == "POST":
        if f.validate_on_submit():
            obj = StockItemType()
            obj.name = f.name.data
            obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
            db.session.add(obj)
            db.session.commit()
            flash("New type added successfully!",'success')
            return redirect(url_for('bp_iwms.stock_item_types'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.stock_item_types'))

@bp_iwms.route('/type_edit/<int:oid>',methods=['GET','POST'])
@login_required
def type_edit(oid):
    obj = StockItemType.query.get_or_404(oid)
    f = TypeEditForm(obj=obj)
    if request.method == "GET":
        context['mm-active'] = 'stock_item_type'
        return admin_edit(f,'bp_iwms.type_edit',oid, \
            model=StockItemType,template='iwms/iwms_edit.html',kwargs={'active':'inventory'})
    elif request.method == "POST":
        if f.validate_on_submit():
            obj.name = f.name.data
            obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
            obj.updated_at = datetime.now()
            db.session.commit()
            flash('Type update Successfully!','success')
            return redirect(url_for('bp_iwms.stock_item_types'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.stock_item_types'))


@bp_iwms.route('/terms')
@login_required
def terms():
    fields = [Term.id,Term.code,Term.description,Term.days]
    context['mm-active'] = 'term'
    return admin_index(Term,fields=fields,form=TermForm(), \
        template='iwms/iwms_index.html', edit_url='bp_iwms.term_edit',\
            create_url="bp_iwms.term_create",kwargs={'active':'inventory'})

@bp_iwms.route('/term_create',methods=['POST'])
@login_required
def term_create():
    f = TermForm()
    if request.method == "POST":
        if f.validate_on_submit():
            obj = Term()
            obj.code = f.code.data
            obj.description = f.description.data
            obj.days = f.days.data if not f.days.data == '' else None
            obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
            db.session.add(obj)
            db.session.commit()
            flash("New term added successfully!",'success')
            return redirect(url_for('bp_iwms.terms'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.terms'))

@bp_iwms.route('/term_edit/<int:oid>',methods=['GET','POST'])
@login_required
def term_edit(oid):
    obj = Term.query.get_or_404(oid)
    f = TermEditForm(obj=obj)
    if request.method == "GET":
        context['mm-active'] = 'term'
        return admin_edit(f,'bp_iwms.term_edit',oid, \
            model=Term,template='iwms/iwms_edit.html',kwargs={'active':'inventory'})
    elif request.method == "POST":
        if f.validate_on_submit():
            obj.code = f.code.data
            obj.description = f.description.data
            obj.days = f.days.data if not f.days.data == '' else None
            obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
            obj.updated_at = datetime.now()
            db.session.commit()
            flash('Term update Successfully!','success')
            return redirect(url_for('bp_iwms.terms'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.terms'))


@bp_iwms.route('/sales_via')
@login_required
def sales_via():
    fields = [SalesVia.id,SalesVia.description]
    context['mm-active'] = 'sales_via'
    return admin_index(SalesVia,fields=fields,form=SalesViaForm(), \
        template='iwms/iwms_index.html', edit_url='bp_iwms.sales_via_edit',\
            create_url="bp_iwms.sales_via_create",kwargs={'active':'sales'})

@bp_iwms.route('/sales_via_create',methods=['POST'])
@login_required
def sales_via_create():
    f = SalesViaForm()
    if request.method == "POST":
        if f.validate_on_submit():
            obj = SalesVia()
            obj.description = f.description.data
            obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
            db.session.add(obj)
            db.session.commit()
            flash("New sales via added successfully!",'success')
            return redirect(url_for('bp_iwms.sales_via'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.sales_via'))

@bp_iwms.route('/sales_via_edit/<int:oid>',methods=['GET','POST'])
@login_required
def sales_via_edit(oid):
    obj = SalesVia.query.get_or_404(oid)
    f = SalesViaEditForm(obj=obj)
    if request.method == "GET":
        context['mm-active'] = 'sales_via'
        return admin_edit(f,'bp_iwms.sales_via_edit',oid, \
            model=SalesVia,template='iwms/iwms_edit.html',kwargs={'active':'sales'})
    elif request.method == "POST":
        if f.validate_on_submit():
            obj.description = f.description.data
            obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
            obj.updated_at = datetime.now()
            db.session.commit()
            flash('Sales via update Successfully!','success')
            return redirect(url_for('bp_iwms.sales_via'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.sales_via'))


@bp_iwms.route('/client_groups')
@login_required
def client_groups():
    fields = [ClientGroup.id,ClientGroup.name,ClientGroup.updated_by,ClientGroup.updated_at]
    context['mm-active'] = 'client_group'
    return admin_index(ClientGroup,fields=fields,form=ClientGroupForm(), \
        template='iwms/iwms_index.html', edit_url='bp_iwms.client_group_edit',\
            create_url="bp_iwms.client_group_create",kwargs={'active':'sales'})

@bp_iwms.route('/client_group_create',methods=['POST'])
@login_required
def client_group_create():
    f = ClientGroupForm()
    if request.method == "POST":
        if f.validate_on_submit():
            obj = ClientGroup()
            obj.name = f.name.data
            obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
            db.session.add(obj)
            db.session.commit()
            flash("New client group added successfully!",'success')
            return redirect(url_for('bp_iwms.client_groups'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.client_groups'))

@bp_iwms.route('/client_group_edit/<int:oid>',methods=['GET','POST'])
@login_required
def client_group_edit(oid):
    obj = ClientGroup.query.get_or_404(oid)
    f = ClienGroupEditForm(obj=obj)
    if request.method == "GET":
        context['mm-active'] = 'client_group'
        return admin_edit(f,'bp_iwms.client_group_edit',oid, \
            model=ClientGroup,template='iwms/iwms_edit.html',kwargs={'active':'sales'})
    elif request.method == "POST":
        if f.validate_on_submit():
            obj.name = f.name.data
            obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
            obj.updated_at = datetime.now()
            db.session.commit()
            flash('Client group update Successfully!','success')
            return redirect(url_for('bp_iwms.client_groups'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.client_groups'))

@bp_iwms.route('/clients')
@login_required
def clients():
    fields = [Client.id,Client.status,Client.code,Client.name,Client.updated_by,Client.updated_at]
    context['mm-active'] = 'client'
    return admin_index(Client,fields=fields,form=ClientForm(), \
        template='iwms/iwms_index.html', edit_url='bp_iwms.client_edit',\
            create_url="bp_iwms.client_create",kwargs={'active':'sales'})

@bp_iwms.route('/client_create',methods=['POST'])
@login_required
def client_create():
    f = ClientForm()
    if request.method == "POST":
        if f.validate_on_submit():
            obj = Client()
            obj.name = f.name.data
            obj.code = f.code.data
            obj.status = "ACTIVE"
            obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
            db.session.add(obj)
            db.session.commit()
            flash("New Client added successfully!",'success')
            return redirect(url_for('bp_iwms.clients'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.clients'))

@bp_iwms.route('/client_edit/<int:oid>',methods=['GET','POST'])
@login_required
def client_edit(oid):
    obj = Client.query.get_or_404(oid)
    f = ClientEditForm(obj=obj)
    if request.method == "GET":
        context['mm-active'] = 'client'
        return admin_edit(f,'bp_iwms.client_edit',oid, \
            model=ClientGroup,template='iwms/iwms_edit.html',kwargs={'active':'sales'})
    elif request.method == "POST":
        if f.validate_on_submit():
            obj.name = f.name.data
            obj.code = f.code.data
            obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
            obj.updated_at = datetime.now()
            db.session.commit()
            flash('Client update Successfully!','success')
            return redirect(url_for('bp_iwms.clients'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.clients'))