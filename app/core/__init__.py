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
    from app.iwms.models import UnitOfMeasure, Source
    from app.auth.models import User

    print("Installing...")

    if platform.system() == "Windows":
        provinces_path = basedir + "\\app" + "\\core" + "\\csv" + "\\provinces.csv"
        cities_path = basedir + "\\app" + "\\core" + "\\csv" + "\\cities.csv"
    elif platform.system() == "Linux":
        provinces_path = basedir + "/app/core/csv/provinces.csv"
        cities_path = basedir + "/app/core/csv/cities.csv"
    else:
        raise Exception

    print("Inserting provinces to database...")
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
    print("Inserting cities to database...")
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

    if not UnitOfMeasure.query.count() > 0:
        print("Inserting unit of measures...")
        pc = UnitOfMeasure()
        pc.code,pc.description = "pc", "pcs"
        db.session.add(pc)
        db.session.commit()
        print("pc unit of measure inserted!")

    if not Source.query.count() > 0:
        print("Inserting sources...")
        s = Source()
        s.name,s.description = "Purchase Order", "Purchase Order"
        db.session.add(s)
        db.session.commit()
        print("Sources inserted!")        

    if not User.query.count() > 0:
        print("Creating a SuperUser/owner...")
        _create_superuser()

    print("Installation complete!")


def _create_superuser():
    from app.auth.models import User
    from app import db
    user = User()
    # FOR DEVELOPMENT ONLY
    # user.fname = input("Enter First name: ")
    # user.lname = input("Enter Last name: ")
    # user.username = input("Enter Username: ")
    # user.email = input("Enter Email: ")
    # user.set_password(input("Enter password: "))
    user.fname = "Admin"
    user.lname = "Administrator"
    user.username = "admin"
    user.email = "admin@admin.com"
    user.set_password("admin")
    user.is_superuser = 1
    user.role_id = 1
    db.session.add(user)
    db.session.commit()
    print("SuperUser Created!")