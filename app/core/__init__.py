from . import models
from app.auth import auth_urls
from flask import Blueprint, request, redirect, url_for, render_template
from flask_login import current_user
import click
# URLS DICTIONARY
core_urls = {
    'index': 'core.index',
}


bp_core = Blueprint('core', __name__)


@bp_core.route('/')
def index():
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for('bp_iwms.dashboard'))
        else:
            return redirect(url_for(auth_urls['login']))

# Create Superuser command
@bp_core.cli.command('create_superuser')
def create_superuser():
    _create_superuser()


@bp_core.cli.command("create_module")
@click.argument("module_name")
def create_module(module_name):
    try:
        import os
        from config import basedir
        from shutil import copyfile
        import platform

        if platform.system() == "Windows":
            module_path = basedir + "\\app" + "\\" + module_name
            templates_path = basedir + "\\app" + "\\" + module_name + "\\" + "templates" + "\\" + module_name 
            core_init_path = basedir + "\\app" + "\\core" + \
                "\\module_template" + "\\__init__.py"
            core_models_path = basedir + "\\app" + \
                "\\core" + "\\module_template" + "\\models.py"
            core_routes_path = basedir + "\\app" + \
                "\\core" + "\\module_template" + "\\routes.py"
        elif platform.system() == "Linux":
            module_path = basedir + "/app" + "/" + module_name
            templates_path = basedir + "/app" + "/" + module_name + "/templates" + "/" + module_name
            core_init_path = basedir + "/app" + "/core" + "/module_template" + "/__init__.py"
            core_models_path = basedir + "/app" + "/core" + "/module_template" + "/models.py"
            core_routes_path = basedir + "/app" + "/core" + "/module_template" + "/routes.py"

        core_file_list = [core_init_path, core_models_path, core_routes_path]

        if not os.path.exists(module_path):
            os.mkdir(module_path)
            os.makedirs(templates_path)
            for file_path in core_file_list:
                file_name = os.path.basename(file_path)
                copyfile(file_path, os.path.join(module_path, file_name))
    except OSError as e:
        print("Creation of the directory %s failed" % module_path)
        print(e)
    else:
        print("Successfully created the directory %s " % module_path)


@bp_core.cli.command("install")
def install():
    from sqlalchemy import text
    import csv
    from config import basedir
    import platform
    from app import db
    from .models import CoreCity,CoreProvince
    from app.auth.models import Role, RolePermission
    from app.iwms.models import UnitOfMeasure, Source, Warehouse, BinLocation, Supplier,\
        StockItemType, Category, Zone, StockItem, Client, Term, ShipVia, StockItemUomLine
    from app.auth.models import User

    print("Installing...")

    if platform.system() == "Windows":
        provinces_path = basedir + "\\app" + "\\core" + "\\csv" + "\\provinces.csv"
        cities_path = basedir + "\\app" + "\\core" + "\\csv" + "\\cities.csv"
        bin_locations_path = basedir + "\\app" + "\\core" + "\\csv" + "\\iwms_bin_location.csv"
        suppliers_path = basedir + "\\app" + "\\core" + "\\csv" + "\\iwms_supplier.csv"
        stock_item_types_path = basedir + "\\app" + "\\core" + "\\csv" + "\\iwms_stock_item_type.csv"
        uom_path = basedir + "\\app" + "\\core" + "\\csv" + "\\iwms_unit_of_measure.csv"
        categories_path = basedir + "\\app" + "\\core" + "\\csv" + "\\iwms_category.csv"
        zones_path = basedir + "\\app" + "\\core" + "\\csv" + "\\iwms_zone.csv"
        stock_items_path = basedir + "\\app" + "\\core" + "\\csv" + "\\iwms_stock_item.csv"
        terms_path = basedir + "\\app" + "\\core" + "\\csv" + "\\iwms_term.csv"
        ship_vias_path = basedir + "\\app" + "\\core" + "\\csv" + "\\iwms_ship_via.csv"
        clients_path = basedir + "\\app" + "\\core" + "\\csv" + "\\iwms_client.csv"
        item_uom_line_path = basedir + "\\app" + "\\core" + "\\csv" + "\\iwms_stock_item_uom_line.csv"
        item_suppliers_path = basedir + "\\app" + "\\core" + "\\csv" + "\\iwms_suppliers.csv"

    elif platform.system() == "Linux":
        provinces_path = basedir + "/app/core/csv/provinces.csv"
        cities_path = basedir + "/app/core/csv/cities.csv"
        bin_locations_path = basedir + "/app/core/csv/iwms_bin_location.csv"
        suppliers_path = basedir + "/app/core/csv/iwms_supplier.csv"
        stock_item_types_path = basedir + "/app/core/csv/iwms_stock_item_type.csv"
        uom_path = basedir + "/app/core/csv/iwms_unit_of_measure.csv"
        categories_path = basedir + "/app/core/csv/iwms_category.csv"
        zones_path = basedir + "/app/core/csv/iwms_zone.csv"
        stock_items_path = basedir + "/app/core/csv/iwms_stock_item.csv"
        terms_path = basedir + "/app/core/csv/iwms_term.csv"
        ship_vias_path = basedir + "/app/core/csv/iwms_ship_via.csv"
        clients_path = basedir + "/app/core/csv/iwms_client.csv"
        item_uom_line_path = basedir + "/app/core/csv/iwms_stock_item_uom_line.csv"
        item_suppliers_path = basedir + "/app/core/csv/iwms_suppliers.csv"
    else:
        raise Exception

    print("Inserting provinces...")
    if CoreProvince.query.count() < 88:
        with open(provinces_path) as f:
            csv_file = csv.reader(f)
            for id,row in enumerate(csv_file):
                if not id == 0:
                    province = CoreProvince()
                    province.id = int(row[0])
                    province.name = row[2]
                    db.session.add(province)
            db.session.commit()
        print("Provinces done!")
    else:
        print("Provinces exists!")
    print("")
    print("Inserting cities...")
    if CoreCity.query.count() < 1647:
        with open(cities_path) as f:
            csv_file = csv.reader(f)
            for id,row in enumerate(csv_file):
                if not id == 0:
                    city = CoreCity()
                    city.id = int(row[0])
                    city.name = row[2]
                    city.province_id = None
                    db.session.add(city)
            db.session.commit()
        print("Cities done!")
    else:
        print("Cities exists!")

    print("Inserting system roles...")
    if Role.query.count() > 0:
        print("Role already inserted!")
    else:
        role = Role()
        role.name = "Individual"
        db.session.add(role)
        db.session.commit()
        print("Individual role inserted!")

    print("Inserting unit of measures...")
    if not UnitOfMeasure.query.count() > 0:
        with open(uom_path) as f:
            csv_file = csv.reader(f)
            for id,row in enumerate(csv_file):
                if not id == 0:
                    uom = UnitOfMeasure()
                    uom.code, uom.description = row[0], row[1]
                    uom.created_by = "System"
                    db.session.add(uom)
            db.session.commit()
        print("Unit of measures done!")
    else:
        print("Unit of measures exists!")

    if not Source.query.count() > 0:
        print("Inserting sources...")
        s = Source()
        s.name,s.description = "Purchase Order", "Purchase Order"
        s.created_by = "System"
        db.session.add(s)
        db.session.commit()
        print("Sources inserted!")
    
    if not Warehouse.query.count() > 0:
        print("Inserting warehouses...")
        fg = Warehouse()
        fg.code,fg.name, fg.main_warehouse, fg.created_by = 'FG','FINISH GOODS', 1,'System'
        cs = Warehouse()
        cs.code, cs.name, cs.main_warehouse, cs.created_by = 'CS','COLD STORAGE', 1,'System'
        db.session.add(fg)
        db.session.add(cs)
        db.session.commit()
        print("Warehouses inserted!")

    print("Inserting zones...")
    if not Zone.query.count() > 0:
        with open(zones_path) as f:
            csv_file = csv.reader(f)
            for id,row in enumerate(csv_file):
                if not id == 0:
                    z = Zone()
                    z.code, z.description = row[0], row[1]
                    z.created_by = "System"
                    db.session.add(z)
            db.session.commit()
        print("Zones done!")
    else:
        print("Zones exists!")

    print("Inserting bin locations...")
    if not BinLocation.query.count() > 0:
        with open(bin_locations_path) as f:
            csv_file = csv.reader(f)
            for id,row in enumerate(csv_file):
                if not id == 0:
                    bl = BinLocation()
                    bl.code = row[0]
                    bl.description = row[1]
                    bl.warehouse_id = row[2]
                    bl.zone_id = row[3]
                    bl.x = row[4]
                    bl.y = row[5]
                    bl.created_by = "System"
                    db.session.add(bl)
            db.session.commit()
        print("Bin locations done!")
    else:
        print("Bin locations exists!")

    print("Inserting suppliers...")
    if not Supplier.query.count() > 0:
        with open(suppliers_path) as f:
            csv_file = csv.reader(f)
            for id, row in enumerate(csv_file):
                if not id == 0:
                    sup = Supplier()
                    sup.code, sup.name = row[0], row[1]
                    sup.status, sup.address = "ACTIVE", row[2]
                    sup.email_address, sup.contact_person = row[3], row[4]
                    sup.created_by = "System"
                    db.session.add(sup)
            db.session.commit()
        print("Suppliers done!")
    else:
        print("Suppliers exists!")

    print("Inserting stock item types...")
    if not StockItemType.query.count() > 0:
        with open(stock_item_types_path) as f:
            csv_file = csv.reader(f)
            for id, row in enumerate(csv_file):
                if not id == 0:
                    sit = StockItemType()
                    sit.name = row[0]
                    sit.created_by = "System"
                    db.session.add(sit)
            
            db.session.commit()
        print("Stock item types done!")
    else:
        print("Stock item types exists!")

    print("Inserting categories...")
    if not Category.query.count() > 0:
        with open(categories_path) as f:
            csv_file = csv.reader(f)
            for id,row in enumerate(csv_file):
                if not id == 0:
                    c = Category()
                    c.code, c.description = row[0], row[1]
                    c.created_by = "System"
                    db.session.add(c)
            db.session.commit()
        print("Categories done!")
    else:
        print("Categories exists!")

    print("Inserting stock items...")
    if not StockItem.query.count() > 0:
        with open(stock_items_path) as f:
            csv_file = csv.reader(f)
            for id,row in enumerate(csv_file):
                if not id == 0:
                    si = StockItem()
                    si.number, si.stock_item_type_id = row[0], row[1]
                    si.category_id, si.brand = row[2], row[3]
                    si.name, si.description = row[4], row[5]
                    si.packaging, si.description_plu = row[6], row[7]
                    si.barcode, si.qty_plu = row[8], row[9]
                    si.length, si.width, si.height = row[10], row[11], row[12]
                    si.unit_id, si.default_cost, si.default_price = row[13], row[14], row[15]
                    si.weight, si.cbm = row[16], row[17]
                    si.has_serial, si.monitor_expiration = 0, 0
                    si.created_by = "System"
                    db.session.add(si)
            db.session.commit()
        print("Stock items done!")
    else:
        print("Stock items exists!")

    print("Inserting terms...")
    if not Term.query.count() > 0:
        with open(terms_path) as f:
            csv_file = csv.reader(f)
            for id,row in enumerate(csv_file):
                if not id == 0:
                    t = Term()
                    t.code, t.description, t.days = row[0], row[1], row[2]
                    t.created_by = "System"
                    db.session.add(t)
            db.session.commit()
        print("Terms done!")
    else:
        print("Terms exists!")
    
    print("Inserting ship vias...")
    if not ShipVia.query.count() > 0:
        with open(ship_vias_path) as f:
            csv_file = csv.reader(f)
            for id,row in enumerate(csv_file):
                if not id == 0:
                    sv = ShipVia()
                    sv.description = row[0]
                    sv.created_by = "System"
                    db.session.add(sv)
            db.session.commit()
        print("Ship vias done!")
    else:
        print("Ship vias exists!")

    print("Inserting clients...")
    if not Client.query.count() > 0:
        with open(clients_path) as f:
            csv_file = csv.reader(f)
            for id,row in enumerate(csv_file):
                if not id == 0:
                    c = Client()
                    c.code, c.name = row[0], row[1]
                    c.term_id, c.ship_via_id = row[2], row[3]
                    c.created_by = "System"
                    db.session.add(c)
            db.session.commit()
        print("Clients done!")
    else:
        print("Clients exists!")

    # print("Inserting item uom lines...")
    # if not StockItemUomLine.query.count() > 0:
    #     with open(item_uom_line_path) as f:
    #         csv_file = csv.reader(f)
    #         for id,row in enumerate(csv_file):
    #             if not id == 0:
    #                 s = StockItemUomLine()
    #                 s.stock_item_id, s.uom_id = row[0], row[1]
    #                 s.created_by = "System"
    #                 db.session.add(s)
    #         db.session.commit()
    #     print("Item uom lines done!")
    # else:
    #     print("Item uom lines exists!")

    if not User.query.count() > 0:
        print("Creating a SuperUser/owner...")
        _create_superuser()

    print("Installation complete!")


def _create_superuser():
    from app.auth.models import User
    from app import db
    user = User()
    user.fname = input("Enter First name: ")
    user.lname = input("Enter Last name: ")
    user.username = input("Enter Username: ")
    user.email = input("Enter Email: ")
    user.set_password(input("Enter password: "))
    # FOR DEVELOPMENT ONLY
    # user.fname = "Admin"
    # user.lname = "Administrator"
    # user.username = "admin"
    # user.email = "admin@admin.com"
    # user.set_password("admin")
    user.is_superuser = 1
    user.role_id = 1
    user.created_by = "System"
    db.session.add(user)
    db.session.commit()
    print("SuperUser Created!")