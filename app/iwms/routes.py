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
            StockItemUomLine,StockReceiptItemLine, PutawayItemLine,Source, ShipVia, ClientGroup, Client, InventoryItem,\
                ItemBinLocations,SalesOrder,SalesOrderLine,Picking,PickingItemLine

from .forms import *
from datetime import datetime
from app.core.models import CoreLog
from app.auth.models import User
import pdfkit
from flask_mail import Message
from sqlalchemy import and_, func, desc
from flask_cors import cross_origin

context['cold_storage_url'] = current_app.config['COLD_STORAGE_URL']

"""----------------------INTERNAL FUNCTIONS-------------------------"""

def _generate_number(prefix, lID):
    generated_number = ""
    if 1 <= lID < 9:
        generated_number = prefix +"0000000" + str(lID+1)
    elif 9 <= lID < 99:
        generated_number = prefix + "000000" + str(lID+1)
    elif 999 <= lID < 9999:
        generated_number = prefix + "00000" + str(lID+1)
    elif 9999 <= lID < 99999:
        generated_number = prefix + "0000" + str(lID+1)
    elif 99999 <= lID < 999999:
        generated_number = prefix + "000" + str(lID+1)
    elif 999999 <= lID < 9999999:
        generated_number = prefix + "00" + str(lID+1)
    elif 9999999 <= lID < 99999999:
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

@bp_iwms.route("/_create_label",methods=['POST'])
def _create_label():
    import os
    basedir = os.path.abspath(os.path.dirname(__file__))
    basedir = basedir + "/pallet_tag/barcodetxtfile.txt"

    _lot_no = request.json['lot_no']
    _expiry_date = request.json['expiry_date']
    _label = request.json['label']
    _quantity = request.json['quantity']
    _sr_number = request.json['sr_number']
    _po_number = request.json['po_number']
    _stock_id = request.json['stock_id']
    _supplier = request.json['supplier']

    stock_item = StockItem.query.get_or_404(_stock_id)
    _description = stock_item.description
    # SR ,PO ,LOTNUM,EXPIRY DAT,Description ,QTY,Supplier ,SR ,number_of_label

    with open(basedir, 'w+') as the_file:
        txt = "{},{},{},{},{},{},{},{},{}".format(_sr_number,_po_number,\
            _lot_no,_expiry_date,_description,_quantity,_supplier,_sr_number,_label)
        the_file.write(txt)
    
    """ Call .bat to generate pallet tag """
    import subprocess

    filepath= r"D:\iWMS\app\iwms\pallet_tag\printPalletTag.bat"
    p = subprocess.Popen(filepath, shell=True, stdout = subprocess.PIPE)

    stdout, stderr = p.communicate()
    print(p.returncode) # is 0 if success

    res = jsonify({'result':True})
    return res

@bp_iwms.route("/_get_suppliers",methods=['POST'])
def _get_suppliers():
    if request.method == 'POST':
        sup_id = request.json['sup_id']
        po_number = request.json.get('po_number','None')
        db_items = StockItem.query.filter(StockItem.suppliers.any(id=sup_id)).all()
        po_line = []
        if not po_number == 'None':
            po = PurchaseOrder.query.filter_by(po_number=po_number).first()
            po_line = [x.stock_item.id for x in po.product_line]
            
        list_items = []
        for item in db_items:
            if item.id not in po_line:
                list_items.append({'id':item.id,'number':item.number,'name':item.name,'description':item.description,'barcode':item.barcode,'default_cost':str(item.default_cost)})
        res = jsonify(items=list_items)
        print(list_items)
        res.status_code = 200
        return res


@bp_iwms.route('/_get_PO_status',methods=['POST'])
def _get_PO_status():
    if request.method == 'POST':
        _id = request.json['id']
        _po = PurchaseOrder.query.get(_id)
        editable = False
        if _po.status == "LOGGED":
            editable = True
        return jsonify({'editable':editable})


@bp_iwms.route('/_get_SO_status',methods=['POST'])
def _get_SO_status():
    if request.method == 'POST':
        _id = request.json['id']
        _so = SalesOrder.query.get(_id)
        editable = False
        if _so.status == "LOGGED":
            editable = True
        return jsonify({'editable':editable})


@bp_iwms.route('/_update_bin_coord', methods=['POST'])
def _update_bin_coord():
    if request.method == 'POST':
        _bin_code = request.json['bin_code']
        _x,_y = request.json['x'], request.json['y']
        print(_x,_y);
        bin = BinLocation.query.filter_by(code=_bin_code).first()
        bin.x = _x / 2
        bin.y = _y / 2
        db.session.commit()
        return jsonify({'Result':True})

@bp_iwms.route('/_get_bin_items',methods=['POST'])
def _get_bin_items():
    if request.method == 'POST':
        _bin_code = request.json['bin_code']
        bin = BinLocation.query.filter_by(code=_bin_code).first()
        items = []
        for x in bin.item_bin_locations:
            items.append({
                'name': x.inventory_item.stock_item.name,
                'qty_on_hand': x.qty_on_hand,
                'lot_no': x.lot_no,
                'expiry_date': x.expiry_date,
            })
        return jsonify(res=items)

@bp_iwms.route('/_create_bin',methods=['POST'])
def _create_bin():
    _bin_code = request.json['bin_code']
    bin = BinLocation()
    bin.code = _bin_code
    bin.x = 0
    bin.y = 0
    db.session.add(bin)
    db.session.commit()
    return jsonify({"Result":True})


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
                'qty':line.qty,
                'remaining_qty':line.remaining_qty,
                'received_qty':line.received_qty
                })
        res = jsonify(items=po_line)
        res.status_code = 200
        return res

def _check_fast_slow(item_id):
    _item_count = InventoryItem.query.count()
    _item_count = _item_count * 0.5
    _top_items = db.session.query(InventoryItem.id)\
        .join(SalesOrderLine.inventory_item).group_by(InventoryItem.id).order_by(func.count(InventoryItem.id).desc()).limit(_item_count).all()

    for x in _top_items:
        if x[0] == item_id:
            return True

    return False

@bp_iwms.route('/_get_bin_locations',methods=['POST'])
def _get_bin_locations():
    if request.method == 'POST':
        _fast_slow = request.json['fast_slow']
        _warehouse_name = request.json['warehouse']
        _bin_list = []
        _warehouse = Warehouse.query.filter_by(name=_warehouse_name).first()
        _cold_storage = Warehouse.query.filter_by(name="COLD STORAGE").first()
        if _fast_slow == 'FAST':
            
            if _warehouse_name == 'COLD STORAGE':
                _bins = BinLocation.query.filter_by(warehouse_id=_warehouse.id).order_by(BinLocation.code).limit(50).all()
            else:
                _bins = BinLocation.query.filter(BinLocation.warehouse_id != _cold_storage.id).order_by(BinLocation.code).limit(50).all()

            for x in _bins:
                _bin_list.append({
                    'id': x.id,
                    'code': x.code,
                })
        elif _fast_slow == 'SLOW':
            if _warehouse_name == 'COLD STORAGE':
                _bins = BinLocation.query.filter_by(warehouse_id=_warehouse.id).order_by(BinLocation.code.desc()).limit(50).all()
            else:
                _bins = BinLocation.query.filter(BinLocation.warehouse_id != _cold_storage.id).order_by(BinLocation.code.desc()).limit(50).all()
            
            for x in _bins:
                _bin_list.append({
                    'id': x.id,
                    'code': x.code,
                })
        else:
            _bins = BinLocation.query.filter(BinLocation.warehouse_id != _cold_storage.id).order_by(BinLocation.code).all()
            for x in _bins:
                _bin_list.append({
                    'id': x.id,
                    'code': x.code,
                })

        return jsonify(bins=_bin_list)


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

                _ii = InventoryItem.query.filter_by(stock_item_id=line.stock_item.id).first()
                if not _ii == None:
                    _ibl = ItemBinLocations.query.with_entities(func.sum(ItemBinLocations.qty_on_hand)).filter_by(inventory_item_id=_ii.id).all()
                else:
                    _ibl = [[0]]

                fast_slow = ""
                if not line.stock_item.inventory_stock_item == []:
                    if _check_fast_slow(line.stock_item.inventory_stock_item[0].id):
                        fast_slow = "FAST"
                    else:
                        fast_slow = "SLOW"

                sr_line.append({
                    'id':line.stock_item.id,'name':line.stock_item.name,
                    'uom':line.uom,'number':line.stock_item.number,
                    'lot_no':line.lot_no,'expiry_date': _expiry_date,
                    'received_qty':line.received_qty,
                    'prev_stored': str(_ibl[0][0]) if not _ibl[0][0] == None else 0,
                    'is_putaway': line.is_putaway,
                    'fast_slow': fast_slow
                    })
        res = jsonify(items=sr_line)
        res.status_code = 200
        return res

@bp_iwms.route('/_get_so_line',methods=['POST'])
def _get_so_line():
    if request.method == "POST":
        so_id = request.json['so_id']
        so = SalesOrder.query.get_or_404(so_id)
        so_line = []

        for line in so.product_line:
            if line:
                _expiry_date = ''
                if line.item_bin_location.expiry_date is not None:
                    _expiry_date = line.item_bin_location.expiry_date.strftime("%Y-%m-%d")

                so_line.append({
                    'id':line.item_bin_location_id,'name':line.inventory_item.stock_item.name,
                    'uom':line.uom.code,'number':line.inventory_item.stock_item.number,
                    'lot_no':line.item_bin_location.lot_no,'expiry_date': _expiry_date,
                    'qty':line.qty,'bin_location': line.item_bin_location.bin_location.code,
                    'issued_qty': line.issued_qty
                    })

        res = jsonify(items=so_line)
        res.status_code = 200
        return res


@bp_iwms.route('/_get_uom_line',methods=['POST'])
def _get_uom_line():
    if request.method == 'POST':
        stock_item_id = request.json['stock_item_id']
        # Pag 0 means kukunin nya lahat ang uom
        if stock_item_id == 0:
            obj = UnitOfMeasure.query.all()
            uom_line = []
            for line in obj:
                uom_line.append({'id':line.id,'code':line.code})
            res = jsonify(uom_lines=uom_line)
            res.status_code = 200
            return res 
        else:
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
    
    """ DATA SA DASHBOARD """
    _qty_on_hand = ItemBinLocations.query.with_entities(func.sum(ItemBinLocations.qty_on_hand)).all()
    _qty_to_be_received = StockReceipt.query.filter_by(status="LOGGED").join(StockReceiptItemLine)\
        .with_entities(func.sum(StockReceiptItemLine.received_qty)).all()
    _all_items = InventoryItem.query.count()
    _to_be_purchased = PurchaseOrder.query.count()
    _to_be_receipted = StockReceipt.query.count()
    _to_be_stored = Putaway.query.count()

    _po_logged = PurchaseOrder.query.filter_by(status="LOGGED").count()
    _po_pending = PurchaseOrder.query.filter_by(status="PENDING").count()
    _po_released = PurchaseOrder.query.filter_by(status="RELEASED").count()
    _po_completed = PurchaseOrder.query.filter_by(status="COMPLETED").count()
    _po_data ={
        'logged': _po_logged,
        'pending': _po_pending,
        'released': _po_released,
        'completed': _po_completed
    }

    _sr_remaining_items = PurchaseOrder.query.filter_by(status="PENDING").join(PurchaseOrderProductLine)\
        .with_entities(func.sum(PurchaseOrderProductLine.remaining_qty)).all()
    _sr_incomplete_items = PurchaseOrder.query.filter(PurchaseOrder.status.in_(["LOGGED","PENDING"]))\
        .join(PurchaseOrderProductLine).filter_by(received_qty=None)\
        .with_entities(func.sum(PurchaseOrderProductLine.remaining_qty)).all()
    _sr_data = {
        'completed': str(_qty_to_be_received[0][0]),
        'remaining': str(_sr_remaining_items[0][0]),
        'incomplete': str(_sr_incomplete_items[0][0]),
    }

    _pwy_data = {
        'to_be_stored_qty': str(_qty_to_be_received[0][0]),
        'stored': str(_qty_on_hand[0][0]),
    }

    _to_be_pick_qty = SalesOrder.query.filter(SalesOrder.status.in_(["LOGGED","ON HOLD"])).join(SalesOrderLine)\
        .with_entities(func.sum(SalesOrderLine.qty)).all()
    _picked_qty = SalesOrder.query.join(SalesOrderLine)\
        .with_entities(func.sum(SalesOrderLine.issued_qty)).all()

    _pck_data = {
        'to_be_pick_qty': str(_to_be_pick_qty[0][0]),
        'picked_qty': str(_picked_qty[0][0]),
    }

    _total_orders = SalesOrder.query.count()
    _items_to_be_confirmed = SalesOrderLine.query.count()
    _items_confirmed = SalesOrderLine.query.join(SalesOrder).filter(SalesOrder.status.in_(["CONFIRMED"]))\
        .count()

    dashboard_data = {
        'qty_on_hand': str(_qty_on_hand[0][0]),
        'qty_to_be_received': str(_qty_to_be_received[0][0]),
        'all_items': _all_items,
        'to_be_purchased': _to_be_purchased,
        'to_be_receipted': _to_be_receipted,
        'to_be_stored': _to_be_stored,
        'po_data': _po_data,
        'sr_data': _sr_data,
        'pwy_data': _pwy_data,
        'total_orders': _total_orders,
        'items_to_be_confirmed': _items_to_be_confirmed,
        'pck_data': _pck_data,
        'items_confirmed': _items_confirmed
    }

    return render_template('iwms/iwms_dashboard.html',context=context,dd=dashboard_data,title="Dashboard")

@bp_iwms.route('/reports')
@login_required
def reports():
    context['module'] = 'iwms'
    context['active'] = 'reports'
    context['mm-active'] = ""

    _top_clients = db.session.query(Client.code,Client.name,func.count(Client.id))\
        .join(SalesOrder.client).group_by(Client.id).order_by(func.count(Client.id).desc()).all()

    _sales_clients = db.session.query(Client.name,func.sum(SalesOrder.total_price))\
        .join(SalesOrder.client).group_by(Client.id).all()

    _sales_clients_dict = []

    for x in _sales_clients:
        _sales_clients_dict.append({
            'name':x[0],
            'sales':str(x[1])
        })

    _pos = PurchaseOrder.query.join(PurchaseOrderProductLine).order_by(PurchaseOrder.po_number.desc()).all()

    _sos = SalesOrder.query.join(SalesOrderLine).order_by(SalesOrder.number.desc()).all()

    _top_items = db.session.query(StockItem.name,StockItem.description,func.count(StockItem.id))\
        .join(PurchaseOrderProductLine.stock_item).group_by(StockItem.id).order_by(func.count(StockItem.id).desc()).all()

    _top_sale_items = db.session.query(StockItem.name,StockItem.description,func.count(InventoryItem.id))\
        .join(InventoryItem, StockItem.id == InventoryItem.stock_item_id)\
        .join(SalesOrderLine, InventoryItem.id == SalesOrderLine.inventory_item_id).group_by(InventoryItem.id).order_by(func.count(InventoryItem.id).desc()).all()

    _low_sale_items = db.session.query(StockItem.name,StockItem.description,func.count(InventoryItem.id))\
        .join(InventoryItem, StockItem.id == InventoryItem.stock_item_id)\
        .join(SalesOrderLine, InventoryItem.id == SalesOrderLine.inventory_item_id).group_by(InventoryItem.id).order_by(func.count(InventoryItem.id)).all()

    _srs = StockReceipt.query.join(StockReceiptItemLine).order_by(StockReceipt.sr_number.desc()).all()

    _item_expiration = ItemBinLocations.query.order_by(desc(ItemBinLocations.expiry_date)).all()

    _item_expiration_list = []
    if _item_expiration:
        for item in _item_expiration:
            status = ''
            if item.expiry_date < datetime.now():
                status = 'EXPIRED'
            else:
                status = 'GOOD'
                
                if (item.expiry_date - datetime.now()).days < 30:
                    status = "NEARLY EXPIRED"

            _item_expiration_list.append([item,status])

    report_data = {
        'top_clients': _top_clients,
        'sales_clients': _sales_clients_dict,
        'pos':_pos,
        'sos': _sos,
        'top_items': _top_items,
        'top_so_items': _top_sale_items,
        'low_so_items': _low_sale_items,
        'srs': _srs,
        'item_expiration': _item_expiration_list
    }

    return render_template('iwms/iwms_reports.html',context=context,title="Reports",rd=report_data)


@bp_iwms.route('/bin_location')
@login_required
def warehouse_bin_location():
    context['active'] = 'warehouse_bin_location'
    context['mm-active'] = 'warehouse_bin_location'
    context['module'] = 'iwms'
    context['model'] = 'warehouse_bin_location'
    bins = BinLocation.query.all()
    return render_template('iwms/iwms_warehouse_bin_location.html',context=context,bins=bins,title="Warehouse Floor Plan")

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
    fields = [Group.id,Group.name,Group.created_by,Group.created_at,Group.updated_by,Group.updated_at]
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
                try:
                    group = Group()
                    group.name = form.name.data
                    group.created_by = "{} {}".format(current_user.fname,current_user.lname)
                    db.session.add(group)
                    db.session.commit()
                    flash('New group added successfully!','success')
                    _log_create('New group added',"GroupID={}".format(group.id))
                    return redirect(url_for('bp_iwms.groups'))
                except Exception as e:
                    flash(str(e),'error')
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
            try:
                group.name = form.name.data
                group.updated_at = datetime.now()
                group.updated_by = "{} {}".format(current_user.fname,current_user.lname)
                db.session.commit()
                flash('Group update Successfully!','success')
                _log_create("Group update","GroupID={}".format(group.id))
                return redirect(url_for('bp_iwms.groups'))
            except Exception as e:
                flash(str(e),'error')
                return redirect(url_for('bp_iwms.groups'))
        else:    
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.groups'))


@bp_iwms.route('/departments')
@login_required
def departments():
    fields = [Department.id,Department.name,Department.created_by,Department.created_at,\
        Department.updated_by,Department.updated_at]
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
                try:
                    dept = Department()
                    dept.name = form.name.data
                    dept.created_by = "{} {}".format(current_user.fname,current_user.lname)
                    db.session.add(dept)
                    db.session.commit()
                    flash('New department added successfully!','success')
                    _log_create('New department added','DepartmentID={}'.format(dept.id))
                    return redirect(url_for('bp_iwms.departments'))
                except Exception as e:
                    flash(str(e),'error')
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
            try:
                obj.name = f.name.data
                obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
                obj.updated_at = datetime.now()
                db.session.commit()
                flash('Department update Successfully!','success')
                _log_create('Department update','DepartmentID={}'.format(oid))
                return redirect(url_for('bp_iwms.departments'))
            except Exception as e:
                flash(str(e),'error')
                return redirect(url_for('bp_iwms.departments'))
        else:    
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.departments'))


@bp_iwms.route("/backup")
@login_required
def backup():
    from .backup import backup
    try:
        _backup,_db = backup()
        return send_from_directory(directory=_backup,filename=_db,as_attachment=True)
    except Exception as e:
        flash(str(e),'error')
        return redirect(url_for('bp_iwms.logs'))


@bp_iwms.route('/logs')
@login_required
def logs():
    from app.auth.models import User
    fields = [CoreLog.id,User.fname,CoreLog.date,CoreLog.description,CoreLog.data]
    models = [CoreLog,User]
    context['mm-active'] = 'logs'
    return admin_index(*models,fields=fields,template='iwms/iwms_index.html',action="iwms/iwms_system_actions.html",create_modal=False,view_modal=False,kwargs={
        'index_title':'System Logs and backup','index_headers':['User','Date','Description','Data'],'index_message':'List of items',
        'active':'system'})

@bp_iwms.route('/warehouses')
@login_required
def warehouses():
    fields = [Warehouse.id,Warehouse.code,Warehouse.name,\
        Warehouse.created_by,Warehouse.created_at,Warehouse.updated_by,Warehouse.updated_at]
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
                try:
                    wh = Warehouse()
                    wh.code = form.code.data
                    wh.name = form.name.data
                    wh.active = 1
                    wh.main_warehouse = 1
                    wh.created_by = "{} {}".format(current_user.fname,current_user.lname)
                    db.session.add(wh)
                    db.session.commit()
                    _log_create('New warehouse added','WarehouseID={}'.format(wh.id))
                    
                    flash("New warehouse added successfully!",'success')
                    return redirect(url_for('bp_iwms.warehouses'))
                except Exception as e:
                    flash(str(e),'error')
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
            try:
                obj.code = f.code.data
                obj.name = f.name.data
                obj.active = 1
                obj.main_warehouse = 1
                obj.updated_at = datetime.now()
                obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
                db.session.commit()
                _log_create('Warehouse update','WarehouseID={}'.format(oid))
                flash('Warehouse update Successfully!','success')
                return redirect(url_for('bp_iwms.warehouses'))
            except Exception as e:
                flash(str(e),'error')
                return redirect(url_for('bp_iwms.warehouses'))
        else:    
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.warehouses'))

@bp_iwms.route('/zones')
@login_required
def zones():
    fields = [Zone.id,Zone.code,Zone.description,Zone.created_by,Zone.created_at,Zone.updated_by,Zone.updated_at]
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
                try:
                    obj = Zone()
                    obj.code = f.code.data
                    obj.description = f.description.data
                    obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
                    db.session.add(obj)
                    db.session.commit()
                    _log_create('New zone added','ZoneID={}'.format(obj.id))
                    flash("New zone added successfully!",'success')
                    return redirect(url_for('bp_iwms.zones'))
                except Exception as e:
                    flash(str(e),'error')
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
            try:
                obj.code = f.code.data
                obj.description = f.description.data
                obj.updated_at = datetime.now()
                obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
                db.session.commit()
                _log_create('Zone update','ZoneID={}'.format(obj.id))
                flash('Zone update Successfully!','success')
                return redirect(url_for('bp_iwms.zones'))
            except Exception as e:
                flash(str(e),'error')
                return redirect(url_for('bp_iwms.zones'))
        else:    
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.zones'))
    

@bp_iwms.route('/bin_locations')
@login_required
def bin_locations():
    fields = [
        BinLocation.id,BinLocation.code,BinLocation.description, \
            Warehouse.name,Zone.code]
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
                try:
                    obj = BinLocation()
                    obj.code = f.code.data
                    obj.description = f.description.data
                    obj.index = f.index.data if not f.index.data == '' else None
                    obj.warehouse_id = f.warehouse_id.data if not f.warehouse_id.data == '' else None
                    obj.zone_id = f.zone_id.data if not f.zone_id.data == '' else None
                    obj.pallet_slot = f.pallet_slot.data if not f.pallet_slot.data == '' else None
                    obj.pallet_cs = f.pallet_cs.data if not f.pallet_cs.data == '' else None
                    obj.capacity = f.capacity.data if not f.capacity.data == '' else None
                    obj.weight_cap = f.weight_cap.data if not f.weight_cap.data == '' else None
                    obj.cbm_cap = f.cbm_cap.data if not f.cbm_cap.data == '' else None
                    obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
                    db.session.add(obj)
                    db.session.commit()
                    _log_create('New bin location added','BinLocationID={}'.format(obj.id))
                    flash("New Bin Location added successfully!",'success')
                    return redirect(url_for('bp_iwms.bin_locations'))
                except Exception as e:
                    flash(str(e),'error')
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
            try:
                obj.code = f.code.data
                obj.description = f.description.data
                obj.index = f.index.data if not f.index.data == '' else None
                obj.warehouse_id = f.warehouse_id.data if not f.warehouse_id.data == '' else None
                obj.zone_id = f.zone_id.data if not f.zone_id.data == '' else None
                obj.pallet_slot = f.pallet_slot.data if not f.pallet_slot.data == '' else None
                obj.pallet_cs = f.pallet_cs.data if not f.pallet_cs.data == '' else None
                obj.capacity = f.capacity.data if not f.capacity.data == '' else None
                obj.weight_cap = f.weight_cap.data if not f.weight_cap.data == '' else None
                obj.cbm_cap = f.cbm_cap.data if not f.cbm_cap.data == '' else None
                obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
                obj.updated_at = datetime.now()
                db.session.commit()
                _log_create('BinLocation update','BinLocationID={}'.format(obj.id))
                flash('Bin Location update Successfully!','success')
                return redirect(url_for('bp_iwms.bin_locations'))
            except Exception as e:
                flash(str(e),'error')
                return redirect(url_for('bp_iwms.bin_locations'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.bin_locations'))

@bp_iwms.route('/categories')
@login_required
def categories():
    fields = [Category.id,Category.code,Category.description,Category.created_by,Category.created_at,\
        Category.updated_by,Category.updated_at]
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
            try:
                obj = Category()
                obj.code = f.code.data
                obj.description = f.description.data
                obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
                db.session.add(obj)
                db.session.commit()
                _log_create('New category added','CategoryID={}'.format(obj.id))
                flash("New Category added successfully!",'success')
                return redirect(url_for('bp_iwms.categories'))
            except Exception as e:
                flash(str(e),'error')
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
            try:
                obj.code = f.code.data
                obj.description = f.description.data
                obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
                obj.updated_at = datetime.now()
                db.session.commit()
                _log_create('Category update','CategoryID={}'.format(obj.id))
                flash('Category update Successfully!','success')
                return redirect(url_for('bp_iwms.categories'))
            except Exception as e:
                flash(str(e),'error')
                return redirect(url_for('bp_iwms.categories'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.categories'))

@bp_iwms.route('/unit_of_measures')
@login_required
def unit_of_measures():
    fields = [UnitOfMeasure.id,UnitOfMeasure.code,UnitOfMeasure.description,UnitOfMeasure.active,\
        UnitOfMeasure.created_by,UnitOfMeasure.created_at,UnitOfMeasure.updated_by,UnitOfMeasure.updated_at]
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
            try:
                obj = UnitOfMeasure()
                obj.code = f.code.data
                obj.description = f.description.data
                obj.active = 1 if f.active.data == 'on' else 0
                obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
                db.session.add(obj)
                db.session.commit()
                _log_create('New unit of measure added','UOMID={}'.format(obj.id))
                flash("New Unit of measure added successfully!",'success')
                return redirect(url_for('bp_iwms.unit_of_measures'))
            except Exception as e:
                flash(str(e),'error')
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
            try:
                obj.code = f.code.data
                obj.description = f.description.data
                obj.active = 1 if f.active.data == 'on' else 0
                obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
                obj.updated_at = datetime.now()
                db.session.commit()
                _log_create('Unit of measure update','UOMID={}'.format(obj.id))
                flash('Unit of measure update Successfully!','success')
                return redirect(url_for('bp_iwms.unit_of_measures'))
            except Exception as e:
                flash(str(e),'error')
                return redirect(url_for('bp_iwms.unit_of_measures'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.unit_of_measures'))


@bp_iwms.route('/sources')
@login_required
def sources():
    fields = [Source.id,Source.name,Source.description,Source.created_by,Source.created_at,Source.updated_by,Source.updated_at]
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
            try:
                obj = Source()
                obj.name = f.name.data
                obj.description = f.description.data
                obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
                db.session.add(obj)
                db.session.commit()
                _log_create('New source added','SourceID={}'.format(obj.id))
                flash("New source added successfully!",'success')
                return redirect(url_for('bp_iwms.sources'))
            except Exception as e:
                flash(str(e),'error')
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
            try:
                obj.name = f.name.data
                obj.description = f.description.data
                obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
                obj.updated_at = datetime.now()
                db.session.commit()
                _log_create('Source update','SourceID={}'.format(obj.id))
                flash('Source update Successfully!','success')
                return redirect(url_for('bp_iwms.sources'))
            except Exception as e:
                flash(str(e),'error')
                return redirect(url_for('bp_iwms.sources'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.sources'))


@bp_iwms.route('/stock_items')
@login_required
def stock_items():
    fields = [StockItem.id,StockItem.number,StockItem.name,StockItem.description,\
        StockItem.created_by,StockItem.created_at,StockItem.updated_by,StockItem.updated_at]
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
            try:
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
                        # qty = request.form.get("qty_{}".format(u_id))
                        # barcode = request.form.get("barcode_{}".format(u_id))
                        # _cost = request.form.get("default_cost_{}".format(u_id))
                        # _price = request.form.get("default_price_{}".format(u_id))
                        # default_cost = _cost if not _cost == '' else None
                        # default_price = _price if not _price == '' else None
                        # length = request.form.get("length_{}".format(u_id))
                        # width = request.form.get("width_{}".format(u_id))
                        # height = request.form.get("height_{}".format(u_id))
                        line = StockItemUomLine(uom=uom,qty=None,barcode=None,default_cost=None,default_price=None,\
                            length=None,width=None,height=None)
                        obj.uom_line.append(line)

                db.session.add(obj)
                db.session.commit()
                _log_create('New stock item added','SIID={}'.format(obj.id))
                flash('New Stock Item added Successfully!','success')
                return redirect(url_for('bp_iwms.stock_items'))
            except Exception as e:
                flash(str(e),'error')
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
            try:
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
                        # qty = request.form.get("qty_{}".format(u_id))
                        # barcode = request.form.get("barcode_{}".format(u_id))
                        # default_cost = request.form.get("default_cost_{}".format(u_id))
                        # default_price = request.form.get("default_price_{}".format(u_id))
                        # length = request.form.get("length_{}".format(u_id))
                        # width = request.form.get("width_{}".format(u_id))
                        # height = request.form.get("height_{}".format(u_id))
                        line = StockItemUomLine(uom=uom,qty=None,barcode=None,default_cost=None,default_price=None,\
                            length=None,width=None,height=None)
                        obj.uom_line.append(line)
                        
                db.session.commit()
                _log_create('Stock item update','SIID={}'.format(obj.id))
                flash('Stock Item updated Successfully!','success')
                return redirect(url_for('bp_iwms.stock_items'))
            except Exception as e:
                flash(str(e),'error')
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
    models = StockReceipt.query.with_entities(*fields).filter(StockReceipt.status.in_(['LOGGED','PENDING'])).all()
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
        po_list = PurchaseOrder.query.filter(PurchaseOrder.status.in_(['LOGGED','PENDING']))
        sources = Source.query.all()
        context['active'] = 'inventory'
        context['mm-active'] = 'stock_receipt'
        context['module'] = 'iwms'
        context['model'] = 'stock_receipt'
        return render_template('iwms/stock_receipt/iwms_stock_receipt_create.html',context=context,po_list=po_list,sources=sources,\
            form=f,title="Create stock receipt",warehouses=warehouses,sr_generated_number=sr_generated_number)
    elif request.method == "POST":
        if f.validate_on_submit():
            try:
                obj = StockReceipt()
                obj.sr_number = sr_generated_number
                po = PurchaseOrder.query.filter_by(po_number=f.po_number.data).first()
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

                """ po.status = RELEASED if no remaining qty in the PO items """
                _remaining = 0
                
                item_list = request.form.getlist('sr_items[]')
                if item_list:
                    for item_id in item_list:

                        """ Add SR confirm PO items """

                        item = StockItem.query.get(item_id)
                        lot_no = request.form.get("lot_no_{}".format(item_id))
                        expiry_date = request.form.get("expiry_date_{}".format(item_id)) if not request.form.get("expiry_date_{}".format(item_id)) == '' else None
                        uom = request.form.get("uom_{}".format(item_id))
                        received_qty = request.form.get("received_qty_{}".format(item_id)) if not request.form.get("received_qty_{}".format(item_id)) == '' else None
                        net_weight = request.form.get("net_weight_{}".format(item_id)) if not request.form.get("net_weight_{}".format(item_id)) == '' else None
                        timestamp = request.form.get("timestamp_{}".format(item_id))
                        line = StockReceiptItemLine(stock_item=item,lot_no=lot_no,expiry_date=expiry_date,\
                            uom=uom,received_qty=received_qty,net_weight=net_weight)
                        obj.item_line.append(line)

                        """ Updates PO remaining qty and received qty product line """

                        for ip in po.product_line:
                            if int(item_id) == ip.stock_item_id:
                                if not ip.received_qty is None:
                                    ip.received_qty = ip.received_qty + int(received_qty)
                                else:
                                    ip.received_qty = int(received_qty)
                                ip.remaining_qty = ip.remaining_qty - int(received_qty)

                for ip in po.product_line:
                    _remaining = _remaining + ip.remaining_qty               

                if _remaining == 0:
                    po.status = "RELEASED"
                else:
                    po.status = "PENDING"

                db.session.add(obj)
                db.session.commit()
                _log_create('New stock receipt added','SRID={}'.format(obj.id))
                flash('New Stock Receipt added Successfully!','success')
                return redirect(url_for('bp_iwms.stock_receipts'))
            except Exception as e:
                flash(str(e),'error')
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
        sr_list = StockReceipt.query.filter(StockReceipt.status.in_(['LOGGED','PENDING']))
        bin_locations = BinLocation.query.all()
        context['active'] = 'inventory'
        context['mm-active'] = 'putaway'
        context['module'] = 'iwms'
        context['model'] = 'putaway'
        return render_template('iwms/putaway/iwms_putaway_create.html',context=context,form=f,title="Create putaway",\
            warehouses=warehouses,pwy_generated_number=pwy_generated_number,sr_list=sr_list,bin_locations=bin_locations)
    elif request.method == "POST":
        if f.validate_on_submit():
            try:
                obj = Putaway()
                sr = StockReceipt.query.filter_by(sr_number=f.sr_number.data).first()
                obj.stock_receipt = sr
                obj.pwy_number = pwy_generated_number
                obj.status = "LOGGED"
                obj.reference = f.reference.data
                obj.remarks = f.remarks.data
                obj.created_by = "{} {}".format(current_user.fname,current_user.lname)

                _remaining = False
                items_list = request.form.getlist('pwy_items[]')
                if items_list:
                    for item_id in items_list:
                        item = StockItem.query.get(item_id)
                        lot_no = request.form.get('lot_no_{}'.format(item_id))
                        expiry_date = request.form.get('expiry_{}'.format(item_id)) if not request.form.get('expiry_{}'.format(item_id)) == '' else None
                        uom = request.form.get('uom_{}'.format(item_id))
                        qty = request.form.get('qty_{}'.format(item_id)) if not request.form.get('qty_{}'.format(item_id)) == '' else None
                        _bin_location_code = request.form.get("bin_location_{}".format(item_id)) if not request.form.get("bin_location_{}".format(item_id)) == '' else None
                        line = PutawayItemLine(stock_item=item,lot_no=lot_no,expiry_date=expiry_date,uom=uom,qty=qty)
                        obj.item_line.append(line)

                        """ SENDING CONFIRM ITEMS TO INVENTORY ITEM """

                        _check_for_item = InventoryItem.query.filter_by(stock_item_id=item_id).first()
                        bin_location = BinLocation.query.filter_by(code=_bin_location_code).first()

                        if _check_for_item is None:
                            inventory_item = InventoryItem()
                            inventory_item.stock_item = item
                            inventory_item.category_id = item.category_id
                            inventory_item.stock_item_type_id = item.stock_item_type_id
                            inventory_item.default_price = item.default_price
                            inventory_item.default_cost = item.default_cost

                            item_location = ItemBinLocations(inventory_item=inventory_item,bin_location=bin_location,\
                                qty_on_hand=qty,expiry_date=expiry_date,lot_no=lot_no)

                            db.session.add(inventory_item)
                            db.session.commit()
                        else:
                            bin_item = ItemBinLocations.query.filter_by(inventory_item_id=_check_for_item.id,bin_location_id=bin_location.id).first()
                            if bin_item is not None:
                                bin_item.qty_on_hand = bin_item.qty_on_hand + int(qty)
                                db.session.commit()
                            else:
                                new_bin_item_location = ItemBinLocations(inventory_item=_check_for_item,\
                                    bin_location=bin_location,qty_on_hand=qty,expiry_date=expiry_date,lot_no=lot_no)
                                db.session.add(new_bin_item_location)
                                db.session.commit()

                        for srp in sr.item_line:
                            if int(item_id) == srp.stock_item_id:
                                srp.is_putaway = True
                                db.session.commit()


                for srp in sr.item_line:
                    if srp.is_putaway == False:
                        _remaining = True

                _po_remaining = False

                for pol in sr.purchase_order.product_line:
                    if pol.remaining_qty > 0 :
                        _po_remaining = True

                if _remaining == False:
                    sr.status = "COMPLETED"
                    if _po_remaining == False:
                        sr.purchase_order.status = "COMPLETED"
                else:
                    sr.status = "PENDING"

                db.session.add(obj)
                db.session.commit()
                _log_create('New putaway added','PWYID={}'.format(obj.id))
                flash('New Putaway added Successfully!','success')
                return redirect(url_for('bp_iwms.putaways'))
            except Exception as e:
                flash(str(e),'error')
                return redirect(url_for('bp_iwms.putaways'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.putaways'))


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
        # TODO: dapat kunin yung ibibigay na id ng database
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
            try:
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
                        line = PurchaseOrderProductLine(stock_item=product,qty=qty,unit_cost=cost,\
                            amount=amount,uom=uom,remaining_qty=qty)
                        po.product_line.append(line)
                db.session.add(po)
                db.session.commit()
                _log_create('New purchase order added','POID={}'.format(po.id))

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

                    msg = Message('Purchase Order', sender = current_app.config['MAIL_USERNAME'], recipients = [po.supplier.email_address])
                    msg.body = "Here attached purchase order quotation"

                    with open(file_path,'rb') as pdf_file:
                        msg.attach(filename=file_path,disposition="attachment",content_type="application/pdf",data=pdf_file.read())
                    mail.send(msg)
                    flash('New Purchase Order added Successfully!','success')
                    return send_from_directory(directory=current_app.config['PDF_FOLDER'],filename=file_name,as_attachment=True)
                else:
                    flash('New Purchase Order added Successfully!','success')
                    return redirect(url_for('bp_iwms.purchase_orders'))
            except Exception as e:
                flash(str(e),'error')
                return redirect(url_for('bp_iwms.purchase_orders'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.purchase_orders'))

@bp_iwms.route('/purchase_order_edit/<int:oid>',methods=['GET','POST'])
@login_required
def purchase_order_edit(oid):
    import platform

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
            try:
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
                        line = PurchaseOrderProductLine(stock_item=product,qty=qty,unit_cost=cost,amount=amount,uom=uom,remaining_qty=qty)
                        po.product_line.append(line)

                db.session.commit()
                _log_create('Purchase order update','POID={}'.format(po.id))
                
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
                    
                    """ SEND EMAIL TO SUPPLIER'S EMAIL ADDRESS AND ATTACHED THE SAVED PDF IN /STATIC/PDFS FOLDER
                    """

                    msg = Message('Purchase Order', sender = current_app.config['MAIL_USERNAME'], recipients = [po.supplier.email_address])
                    msg.body = "Here attached purchase order quotation"

                    with open(file_path,'rb') as pdf_file:
                        msg.attach(filename=file_path,disposition="attachment",content_type="application/pdf",data=pdf_file.read())
                    mail.send(msg)
                                
                    flash('Purchase Order updated Successfully!','success')
                    return send_from_directory(directory=current_app.config['PDF_FOLDER'],filename=file_name,as_attachment=True)

                flash('Purchase Order updated Successfully!','success')
                return redirect(url_for('bp_iwms.purchase_orders'))
            except Exception as e:
                flash(str(e),'error')
                return redirect(url_for('bp_iwms.purchase_orders'))            
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.purchase_orders'))

@bp_iwms.route('/purchase_order_view/<int:oid>')
@login_required
def purchase_order_view(oid):
    """ First view function for viewing only and not editable html """
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

        return render_template('iwms/purchase_order/iwms_purchase_order_view.html', oid=oid,stock_items='',line_items=po.product_line, \
            context=context,form=f,title="View purchase order",warehouses=warehouses,suppliers=suppliers)


@bp_iwms.route('/suppliers')
@login_required
def suppliers():
    fields = [Supplier.id,Supplier.code,Supplier.name,Supplier.created_by,Supplier.created_at,Supplier.updated_by,Supplier.updated_at]
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
            try:
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
                _log_create('New supplier added','SUPID={}'.format(obj.id))
                flash("New supplier added successfully!",'success')
                return redirect(url_for('bp_iwms.suppliers'))
            except Exception as e:
                flash(str(e),'error')
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
            try:
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
                _log_create('Supplier update','SUPID={}'.format(obj.id))
                flash('Supplier update Successfully!','success')
                return redirect(url_for('bp_iwms.suppliers'))
            except Exception as e:
                flash(str(e),'error')
                return redirect(url_for('bp_iwms.suppliers'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.suppliers'))


@bp_iwms.route('/stock_item_types')
@login_required
def stock_item_types():
    fields = [StockItemType.id,StockItemType.name,StockItemType.created_by,\
        StockItemType.created_at,StockItemType.updated_by,StockItemType.updated_at]
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
            try:
                obj = StockItemType()
                obj.name = f.name.data
                obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
                db.session.add(obj)
                db.session.commit()
                _log_create('New type added','TypeID={}'.format(obj.id))
                flash("New type added successfully!",'success')
                return redirect(url_for('bp_iwms.stock_item_types'))
            except Exception as e:
                flash(str(e),'error')
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
            try:
                obj.name = f.name.data
                obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
                obj.updated_at = datetime.now()
                db.session.commit()
                _log_create('Type update','TypeID={}'.format(obj.id))
                flash('Type update Successfully!','success')
                return redirect(url_for('bp_iwms.stock_item_types'))
            except Exception as e:
                flash(str(e),'error')
                return redirect(url_for('bp_iwms.stock_item_types'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.stock_item_types'))


@bp_iwms.route('/terms')
@login_required
def terms():
    fields = [Term.id,Term.code,Term.description,Term.days,Term.created_by,Term.created_at,Term.updated_by,Term.updated_at]
    context['mm-active'] = 'term'
    return admin_index(Term,fields=fields,form=TermForm(), \
        template='iwms/iwms_index.html', edit_url='bp_iwms.term_edit',\
            create_url="bp_iwms.term_create",kwargs={'active':'sales'})

@bp_iwms.route('/term_create',methods=['POST'])
@login_required
def term_create():
    f = TermForm()
    if request.method == "POST":
        if f.validate_on_submit():
            try:
                obj = Term()
                obj.code = f.code.data
                obj.description = f.description.data
                obj.days = f.days.data if not f.days.data == '' else None
                obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
                db.session.add(obj)
                db.session.commit()
                _log_create('New term added','TermID={}'.format(obj.id))
                flash("New term added successfully!",'success')
                return redirect(url_for('bp_iwms.terms'))
            except Exception as e:
                flash(str(e),'error')
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
            try:
                obj.code = f.code.data
                obj.description = f.description.data
                obj.days = f.days.data if not f.days.data == '' else None
                obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
                obj.updated_at = datetime.now()
                db.session.commit()
                _log_create('Term update','TermID={}'.format(obj.id))
                flash('Term update Successfully!','success')
                return redirect(url_for('bp_iwms.terms'))
            except Exception as e:
                flash(str(e),'error')
                return redirect(url_for('bp_iwms.terms'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.terms'))


@bp_iwms.route('/ship_via')
@login_required
def ship_via():
    fields = [ShipVia.id,ShipVia.description,ShipVia.created_by,ShipVia.created_at,ShipVia.updated_by,ShipVia.updated_at]
    context['mm-active'] = 'ship_via'
    return admin_index(ShipVia,fields=fields,form=SalesViaForm(), \
        template='iwms/iwms_index.html', edit_url='bp_iwms.sales_via_edit',\
            create_url="bp_iwms.sales_via_create",kwargs={'active':'sales'})

@bp_iwms.route('/sales_via_create',methods=['POST'])
@login_required
def sales_via_create():
    f = SalesViaForm()
    if request.method == "POST":
        if f.validate_on_submit():
            try:
                obj = ShipVia()
                obj.description = f.description.data
                obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
                db.session.add(obj)
                db.session.commit()
                _log_create('New ship via added','ShipViaID={}'.format(obj.id))
                flash("New ship via added successfully!",'success')
                return redirect(url_for('bp_iwms.ship_via'))
            except Exception as e:
                flash(str(e),'error')
                return redirect(url_for('bp_iwms.ship_via'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.ship_via'))

@bp_iwms.route('/sales_via_edit/<int:oid>',methods=['GET','POST'])
@login_required
def sales_via_edit(oid):
    obj = ShipVia.query.get_or_404(oid)
    f = SalesViaEditForm(obj=obj)
    if request.method == "GET":
        context['mm-active'] = 'sales_via'
        return admin_edit(f,'bp_iwms.sales_via_edit',oid, \
            model=ShipVia,template='iwms/iwms_edit.html',kwargs={'active':'sales'})
    elif request.method == "POST":
        if f.validate_on_submit():
            try:
                obj.description = f.description.data
                obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
                obj.updated_at = datetime.now()
                db.session.commit()
                _log_create('Ship via update','ShipViaID={}'.format(obj.id))
                flash('Ship via update Successfully!','success')
                return redirect(url_for('bp_iwms.ship_via'))
            except Exception as e:
                flash(str(e),'error')
                return redirect(url_for('bp_iwms.ship_via'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.ship_via'))


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
            _log_create('New client group added','ClientGroupID={}'.format(obj.id))
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
            _log_create('Client group update','ClientGroupID={}'.format(obj.id))
            flash('Client group update Successfully!','success')
            return redirect(url_for('bp_iwms.client_groups'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.client_groups'))

@bp_iwms.route('/clients')
@login_required
def clients():
    fields = [Client.id,Client.code,Client.name,Client.created_by,Client.created_at,Client.updated_by,Client.updated_at]
    form = ClientForm()
    cli_generated_number = ""
    cli = db.session.query(Client).order_by(Client.id.desc()).first()
    if cli:
        cli_generated_number = _generate_number("CLI",cli.id)
    else:
        # MAY issue to kasi kapag hindi na truncate yung table magkaiba na yung id at number ng po
        # Make sure nakatruncate ang mga table ng po para reset yung auto increment na id
        cli_generated_number = "CLI00000001"
    form.code.auto_generated = cli_generated_number
    context['mm-active'] = 'client'
    return admin_index(Client,fields=fields,form=form, \
        template='iwms/iwms_index.html', edit_url='bp_iwms.client_edit',\
            create_url="bp_iwms.client_create",kwargs={'active':'sales'})

@bp_iwms.route('/client_create',methods=['POST'])
@login_required
def client_create():
    f = ClientForm()
    if request.method == "POST":
        if f.validate_on_submit():
            try:
                obj = Client()
                obj.name = f.name.data
                obj.code = f.code.data
                obj.term_id = f.term_id.data if not f.term_id.data == '' else None
                obj.ship_via_id = f.ship_via_id.data if not f.ship_via_id.data == '' else None
                obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
                db.session.add(obj)
                db.session.commit()
                _log_create('New client added','ClientID={}'.format(obj.id))
                flash("New Client added successfully!",'success')
                return redirect(url_for('bp_iwms.clients'))
            except Exception as e:
                flash(str(e),'error')
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
            try:
                obj.name = f.name.data
                obj.code = f.code.data
                obj.term_id = f.term_id.data if not f.term_id.data == '' else None
                obj.ship_via_id = f.ship_via_id.data if not f.ship_via_id.data == '' else None
                obj.updated_by = "{} {}".format(current_user.fname,current_user.lname)
                obj.updated_at = datetime.now()
                db.session.commit()
                _log_create('Client update','ClientID={}'.format(obj.id))
                flash('Client update Successfully!','success')
                return redirect(url_for('bp_iwms.clients'))
            except Exception as e:
                flash(str(e),'error')
                return redirect(url_for('bp_iwms.clients'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.clients'))


@bp_iwms.route('/inventory_items')
@login_required
def inventory_items():
    fields = [InventoryItem.id,InventoryItem.default_cost,InventoryItem.default_price,StockItem.name,StockItemType.name,Category.description]
    query1 = db.session.query(InventoryItem,StockItem,StockItemType,Category)
    models = query1.outerjoin(StockItem, InventoryItem.stock_item_id == StockItem.id).outerjoin(StockItemType, InventoryItem.stock_item_type_id == StockItemType.id).\
        outerjoin(Category, InventoryItem.category_id  == Category.id).\
            with_entities(InventoryItem.id,StockItem.name,InventoryItem.default_cost,InventoryItem.default_price,StockItemType.name,Category.description).all()    
    # Dahil hindi ko masyadong kabisado ang ORM, ito muna
    mmodels = [list(ii) for ii in models]

    for ii in mmodels:
        _ibl = ItemBinLocations.query.with_entities(func.sum(ItemBinLocations.qty_on_hand)).filter_by(inventory_item_id=ii[0]).all()
        ii.append(_ibl[0][0])
        
    context['mm-active'] = 'inventory_item'
    return admin_index(InventoryItem,fields=fields,form=InventoryItemForm(), \
        template='iwms/inventory_item/iwms_inventory_item_index.html',edit_url="bp_iwms.inventory_item_edit",\
            create_modal=True,view_modal="iwms/inventory_item/iwms_inventory_item_view_modal.html",create_url=False,kwargs={'active':'inventory',
            'models': mmodels
            })


@bp_iwms.route('/stock_transfers')
@login_required
def stock_transfers():
    fields = [InventoryItem.id,InventoryItem.default_cost,InventoryItem.default_price,StockItem.name,StockItemType.name,Category.description]
    query1 = db.session.query(InventoryItem,StockItem,StockItemType,Category)
    models = query1.outerjoin(StockItem, InventoryItem.stock_item_id == StockItem.id).outerjoin(StockItemType, InventoryItem.stock_item_type_id == StockItemType.id).\
        outerjoin(Category, InventoryItem.category_id  == Category.id).\
            with_entities(InventoryItem.id,StockItem.name,InventoryItem.default_cost,InventoryItem.default_price,StockItemType.name,Category.description).all()    
    # Dahil hindi ko masyadong kabisado ang ORM, ito muna
    mmodels = [list(ii) for ii in models]

    for ii in mmodels:
        _ibl = ItemBinLocations.query.with_entities(func.sum(ItemBinLocations.qty_on_hand)).filter_by(inventory_item_id=ii[0]).all()
        ii.append(_ibl[0][0])
        
    context['mm-active'] = 'stock_transfer'
    return admin_index(InventoryItem,fields=fields,form=StockTransferForm(), \
        template='iwms/stock_transfer/iwms_stock_transfer_index.html',edit_url="bp_iwms.stock_transfer_edit",\
            create_modal=True,view_modal="iwms/stock_transfer/iwms_stock_transfer_view_modal.html",create_url=False,kwargs={'active':'inventory',
            'models': mmodels
            })


@bp_iwms.route('/stock_transfer_edit/<int:oid>',methods=['GET'])
@login_required
def stock_transfer_edit(oid):
    ii = InventoryItem.query.get_or_404(oid)
    f = InventoryItemEditForm(obj=ii)
    if request.method == "GET":
        # Hardcoded html ang irerender natin hindi yung builtin ng admin
        context['active'] = 'inventory'
        context['mm-active'] = 'inventory_item'
        context['module'] = 'iwms'
        context['model'] = 'inventory_item'
        categories = Category.query.all()
        types = StockItemType.query.all()

        stocks = ItemBinLocations.query.filter_by(inventory_item_id=oid).all()
        bin_locations = BinLocation.query.all()

        return render_template('iwms/stock_transfer/iwms_stock_transfer_edit.html', oid=oid,context=context,form=f,stocks=stocks,\
            title="Transfer stock",number=ii.stock_item.number,name=ii.stock_item.name,categories=categories,types=types,bin_locations=bin_locations)


@bp_iwms.route('/_transfer_location',methods=['POST'])
@login_required
def _transfer_location():
    if request.method == 'POST':
        _item_bin_location_id = request.json['item_bin_location_id']
        _new_bin_location_id = request.json['new_bin_location_id']
        item_bin_location = ItemBinLocations.query.get_or_404(_item_bin_location_id)
        _old_location = item_bin_location.bin_location.code

        item_bin_location.bin_location_id = _new_bin_location_id
        db.session.commit()

        msg = Message('Transfer Location', sender = current_app.config['MAIL_USERNAME'], recipients = ["iwarehouseonline2020@gmail.com"])
        msg.body = "Your stock items - ({}) was transferred to better bin location from {} to {}."\
            .format(item_bin_location.inventory_item.stock_item.name,_old_location,item_bin_location.bin_location.code)
        mail.send(msg)

        resp = jsonify({'result':True})
        resp.headers.add('Access-Control-Allow-Origin', '*')
        resp.status_code = 200
        return resp


@bp_iwms.route('/_get_ii_view_modal_data',methods=["POST"])
@cross_origin()
def get_ii_view_modal_data():
    id = request.json['id']
    # query = "select {} from {} where id = {} limit 1".format(column,table,id)
    # sql = text(query)
    # row = db.engine.execute(sql)
    # res = [x[0] if x[0] is not None else '' for x in row]

    # resp = jsonify(result=str(res[0]),column=column)
    res = {}
    ii = InventoryItem.query.get_or_404(id)
    res['name'] = ii.stock_item.name
    res['number'] = ii.stock_item.number
    res['price'] = str(ii.default_price)
    res['cost'] = str(ii.default_cost)
    res['stock_item_type_id'] = ii.stock_item_type_id
    res['category_id'] = ii.category_id
    print(res)
    resp = jsonify(result=res)
    resp.headers.add('Access-Control-Allow-Origin', '*')
    resp.status_code = 200
    return resp


@bp_iwms.route('/inventory_item_edit/<int:oid>',methods=['GET','POST'])
@login_required
def inventory_item_edit(oid):
    ii = InventoryItem.query.get_or_404(oid)
    f = InventoryItemEditForm(obj=ii)
    if request.method == "GET":
        # Hardcoded html ang irerender natin hindi yung builtin ng admin
        context['active'] = 'inventory'
        context['mm-active'] = 'inventory_item'
        context['module'] = 'iwms'
        context['model'] = 'inventory_item'
        categories = Category.query.all()
        types = StockItemType.query.all()

        stocks = ItemBinLocations.query.filter_by(inventory_item_id=oid).all()

        return render_template('iwms/inventory_item/iwms_inventory_item_edit.html', oid=oid,context=context,form=f,stocks=stocks,\
            title="View inventory item",number=ii.stock_item.number,name=ii.stock_item.name,categories=categories,types=types)
    elif request.method == "POST":
        if f.validate_on_submit():
            ii.default_price = f.default_price.data
            ii.default_cost = f.default_cost.data
            ii.stock_item_type_id = f.stock_item_type_id.data if not f.stock_item_type_id.data == '' else None
            ii.category_id = f.category_id.data if not f.category_id.data == '' else None
            ii.updated_by = "{} {}".format(current_user.fname,current_user.lname)
            ii.updated_at = datetime.now()
            db.session.commit()
            flash('Inventory Item update Successfully!','success')
            return redirect(url_for('bp_iwms.inventory_items'))
        else:
            for key, value in form.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.inventory_items'))

@bp_iwms.route('/sales_orders')
@login_required
def sales_orders():
    fields = [SalesOrder.id,SalesOrder.number,SalesOrder.created_at,SalesOrder.created_by,SalesOrder.status]
    context['mm-active'] = 'sales_order'
    context['create_modal']['create_url'] = False
    return admin_index(SalesOrder,fields=fields,form=SalesOrderViewForm(),create_modal=True,\
        template="iwms/iwms_index.html",kwargs={'active':'sales'},edit_url="bp_iwms.sales_order_edit")


@bp_iwms.route('/sales_order_create',methods=['GET','POST'])
@login_required
def sales_order_create():
    so_generated_number = ""
    so = db.session.query(SalesOrder).order_by(SalesOrder.id.desc()).first()
    if so:
        so_generated_number = _generate_number("SO",so.id)
    else:
        # MAY issue to kasi kapag hindi na truncate yung table magkaiba na yung id at number ng po
        # Make sure nakatruncate ang mga table ng po para reset yung auto increment na id
        so_generated_number = "SO00000001"

    f = SalesOrderCreateForm()
    if request.method == "GET":
        # Hardcoded html ang irerender natin hindi yung builtin ng admin
        clients = Client.query.all()
        terms = Term.query.all()
        ship_vias = ShipVia.query.all()
        items = ItemBinLocations.query.filter(ItemBinLocations.qty_on_hand>0).all()

        context['active'] = 'sales'
        context['mm-active'] = 'sales_order'
        context['module'] = 'iwms'
        context['model'] = 'sales_order'
        return render_template('iwms/sales_order/iwms_sales_order_create.html',context=context,form=f,title="Create sales order"\
            ,so_generated_number=so_generated_number,clients=clients,terms=terms,ship_vias=ship_vias,inventory_items=items)
    elif request.method == "POST":
        if f.validate_on_submit():
            try:
                if f.client_name.data == '':
                    raise Exception('No Customer included')
                r = request.form
                so = SalesOrder()
                so.number = so_generated_number
                client = Client.query.filter_by(name=f.client_name.data).first()
                so.client = client
                so.ship_to = f.ship_to.data
                so.end_user = f.end_user.data
                so.tax_info = f.tax_info.data
                so.reference = f.reference.data
                so.sales_representative = f.sales_representative.data
                so.inco_terms = f.inco_terms.data
                so.destination_port = f.destination_port.data
                so.term_id = None
                so.ship_via_id = None
                so.order_date = f.order_date.data if not f.order_date.data == '' else None
                so.delivery_date = f.delivery_date.data if not f.delivery_date.data == '' else None
                so.remarks = f.remarks.data
                so.approved_by = f.approved_by.data
                so.created_by = "{} {}".format(current_user.fname,current_user.lname)
                
                _total_price = 0
                product_list = r.getlist('products[]')
                if product_list:
                    for product_id in product_list:
                        item_bin_location= ItemBinLocations.query.get_or_404(product_id)
                        product = InventoryItem.query.get_or_404(item_bin_location.inventory_item.id)
                        qty = r.get("qty_{}".format(product_id))
                        unit_price = r.get("price_{}".format(product_id))
                        uom = UnitOfMeasure.query.get(r.get("uom_{}".format(product_id)))
                        line = SalesOrderLine(inventory_item=product,item_bin_location=item_bin_location,\
                            qty=qty,uom=uom,unit_price=unit_price,issued_qty=0)
                        _subtotal = int(qty) * float(line.unit_price)
                        _total_price += _subtotal
                        so.product_line.append(line)

                so.total_price = _total_price

                db.session.add(so)
                db.session.commit()
                _log_create('New sales order added','SOID={}'.format(so.id))
                flash('New Sales Order added Successfully!','success')
                return redirect(url_for('bp_iwms.sales_orders'))
            except Exception as e:
                flash(str(e),'error')
                return redirect(url_for('bp_iwms.sales_orders'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.sales_orders'))


@bp_iwms.route('/sales_order_edit/<int:oid>',methods=['GET','POST'])
@login_required
def sales_order_edit(oid):
    so = SalesOrder.query.get_or_404(oid)
    f = SalesOrderCreateForm(obj=so)
    if request.method == "GET":
        clients = Client.query.all()
        _so_items = [x.item_bin_location_id for x in so.product_line]
        items = ItemBinLocations.query.filter(ItemBinLocations.qty_on_hand>0, ~ItemBinLocations.id.in_(_so_items)).all()
        f.client_name.data = so.client.name if not so.client == None else ''
        if so.client is None:
            f.term_id.data = ''
            f.ship_via_id.data = ''
        else:
            f.term_id.data = so.client.term.description if not so.client.term == None else ''
            f.ship_via_id.data = so.client.ship_via.description if not so.client.ship_via == None else ''
        context['active'] = 'sales'
        context['mm-active'] = 'sales_order'
        context['module'] = 'iwms'
        context['model'] = 'sales_order'

        return render_template('iwms/sales_order/iwms_sales_order_edit.html', oid=oid,\
            context=context,form=f,title="Edit sales order",clients=clients,inventory_items=items,line_items=so.product_line)
    
    elif request.method == "POST":
        if f.validate_on_submit():
            try:
                if f.client_name.data == '':
                    raise Exception('No Customer included')

                r = request.form
                client = Client.query.filter_by(name=f.client_name.data).first()
                so.client = client
                so.ship_to = f.ship_to.data
                so.end_user = f.end_user.data
                so.tax_info = f.tax_info.data
                so.reference = f.reference.data
                so.sales_representative = f.sales_representative.data
                so.inco_terms = f.inco_terms.data
                so.destination_port = f.destination_port.data
                so.term_id = None
                so.ship_via_id = None
                so.order_date = f.order_date.data if not f.order_date.data == '' else None
                so.delivery_date = f.delivery_date.data if not f.delivery_date.data == '' else None
                so.remarks = f.remarks.data
                so.approved_by = f.approved_by.data
                so.updated_by = "{} {}".format(current_user.fname,current_user.lname)

                _total_price = 0
                product_list = r.getlist('products[]')
                if product_list:
                    so.product_line = []
                    for product_id in product_list:
                        item_bin_location= ItemBinLocations.query.get_or_404(product_id)
                        product = InventoryItem.query.get_or_404(item_bin_location.inventory_item.id)
                        qty = r.get("qty_{}".format(product_id))
                        unit_price = r.get("price_{}".format(product_id))
                        uom = UnitOfMeasure.query.get(r.get("uom_{}".format(product_id)))
                        line = SalesOrderLine(inventory_item=product,item_bin_location=item_bin_location,\
                            qty=qty,uom=uom,unit_price=unit_price,issued_qty=0)

                        _total_price = _total_price + float(line.unit_price)
                        so.product_line.append(line)

                so.total_price = _total_price

                db.session.commit()
                _log_create('Sales order update','SOID={}'.format(so.id))
                flash('Sales Order updated Successfully!','success')
                return redirect(url_for('bp_iwms.sales_orders'))
            except Exception as e:
                flash(str(e),'error')
                return redirect(url_for('bp_iwms.sales_orders'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.sales_orders'))


@bp_iwms.route('/sales_order_view/<int:oid>')
@login_required
def sales_order_view(oid):
    """ First view function for viewing only and not editable html """
    so = SalesOrder.query.get_or_404(oid)
    f = SalesOrderCreateForm(obj=so)
    if request.method == "GET":
        clients = Client.query.all()
        _so_items = [x.item_bin_location_id for x in so.product_line]
        items = ItemBinLocations.query.filter(ItemBinLocations.qty_on_hand>0, ~ItemBinLocations.id.in_(_so_items)).all()
        f.client_name.data = so.client.name if not so.client == None else ''
        if so.client is None:
            f.term_id.data = ''
            f.ship_via_id.data = ''
        else:
            f.term_id.data = so.client.term.description if not so.client.term == None else ''
            f.ship_via_id.data = so.client.ship_via.description if not so.client.ship_via == None else ''
        context['active'] = 'sales'
        context['mm-active'] = 'sales_order'
        context['module'] = 'iwms'
        context['model'] = 'sales_order'

        return render_template('iwms/sales_order/iwms_sales_order_view.html', oid=oid,\
            context=context,form=f,title="View sales order",clients=clients,inventory_items=items,line_items=so.product_line)
    

@bp_iwms.route('/pickings')
@login_required
def pickings():
    fields = [Picking.id,Picking.number,Picking.created_by,Picking.created_at,Picking.status]
    context['mm-active'] = 'picking'
    context['create_modal']['create_url'] = False
    return admin_index(Picking,fields=fields,form=PickingIndexForm(),\
        create_modal=True,template="iwms/iwms_index.html",kwargs={'active':'inventory'})


@bp_iwms.route('/picking_create',methods=['GET','POST'])
@login_required
def picking_create():
    pck_generated_number = ""
    pck = db.session.query(Picking).order_by(Picking.id.desc()).first()
    if pck:
        pck_generated_number = _generate_number("PCK",pck.id)
    else:
        # MAY issue to kasi kapag hindi na truncate yung table magkaiba na yung id at number ng po
        # Make sure nakatruncate ang mga table ng po para reset yung auto increment na id
        pck_generated_number = "PCK00000001"

    f = PickingCreateForm()
    if request.method == "GET":
        # Hardcoded html ang irerender natin hindi yung builtin ng admin
        warehouses = Warehouse.query.all()
        sales_orders = SalesOrder.query.filter(SalesOrder.status.in_(['ON HOLD','LOGGED']))
        context['active'] = 'inventory'
        context['mm-active'] = 'picking'
        context['module'] = 'iwms'
        context['model'] = 'picking'
        
        return render_template('iwms/picking/iwms_picking_create.html',context=context,form=f,title="Create picking"\
            ,pck_generated_number=pck_generated_number,warehouses=warehouses,sales_orders=sales_orders)
    elif request.method == "POST":
        if f.validate_on_submit():
            try:
                obj = Picking()
                so = SalesOrder.query.filter_by(number=f.so_number.data).first()
                obj.sales_order = so
                obj.number = pck_generated_number
                obj.status = "LOGGED"
                obj.remarks = f.remarks.data
                obj.created_by = "{} {}".format(current_user.fname,current_user.lname)
                
                _remaining = 0
                items_list = request.form.getlist('pick_items[]')
                if items_list:
                    for item_id in items_list:
                        bin_item = ItemBinLocations.query.get_or_404(item_id)
                        lot_no = request.form.get('lot_no_{}'.format(item_id))
                        expiry_date = request.form.get('expiry_{}'.format(item_id)) if not request.form.get('expiry_{}'.format(item_id)) == '' else None
                        uom = request.form.get('uom_{}'.format(item_id))
                        qty = request.form.get('qty_{}'.format(item_id)) if not request.form.get('qty_{}'.format(item_id)) == '' else None
                        line = PickingItemLine(item_bin_location=bin_item,lot_no=lot_no,expiry_date=expiry_date,uom=uom,qty=qty)
                        obj.item_line.append(line)

                        """ DEDUCTING QUANTITY TO THE PICKED ITEMS """

                        bin_item.qty_on_hand = bin_item.qty_on_hand - int(qty)
                      
                        for pi in so.product_line:

                            if int(item_id) == pi.item_bin_location_id:
                                pi.issued_qty = pi.issued_qty + int(qty)
                                pi.qty = pi.qty - int(qty)
                                db.session.commit()

                for pi in so.product_line:
                    _remaining = _remaining + pi.qty               

                if _remaining == 0:
                    so.status = "CONFIRMED"
                else:
                    so.status = "ON HOLD"

                db.session.add(obj)
                db.session.commit()
                _log_create('New picking added','PCKID={}'.format(obj.id))
                flash('New Picking added Successfully!','success')
                return redirect(url_for('bp_iwms.pickings'))
            except Exception as e:
                flash(str(e),'error')
                return redirect(url_for('bp_iwms.pickings'))
        else:
            for key, value in f.errors.items():
                flash(str(key) + str(value), 'error')
            return redirect(url_for('bp_iwms.pickings'))
