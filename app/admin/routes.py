""" MODULE: ADMIN.ROUTES """
""" FLASK IMPORTS """
from flask import render_template, flash, redirect, url_for, request, current_app,g,jsonify
from flask_login import login_required, current_user
"""--------------END--------------"""

""" APP IMPORTS  """
from app.admin import bp_admin

"""--------------END--------------"""

""" TEMPLATES IMPORTS """
from . import admin_templates
"""--------------END--------------"""

from app import context
from app.core.models import HomeBestModel,HomeBestModule
from sqlalchemy import text
from flask_cors import cross_origin
from app import db

# TODO: Para ito sa pag delete dito mag sstore index_url ng kung anong dinelete, 
# issue to kapag rekta inopen yung edit page sa url address
index_url = ""

# @bp_admin.route('/')
# @login_required
# def dashboard():
#     return admin_dashboard()


@bp_admin.route('/apps')
def apps():
    context['active'] = 'apps'
    context['module'] = 'admin'
    modules = HomeBestModule.query.all()

    return render_template('admin/admin_apps.html',context=context,title='Apps',modules=modules)


@bp_admin.route('/delete/<string:delete_table>/<int:oid>',methods=['POST'])
@login_required
def delete(delete_table,oid):
    try:
        index_url = request.args.get('index_url')
        query = "DELETE from {} where id = {}".format(delete_table,oid)
        db.engine.execute(text(query))
        flash('Deleted Successfully!','success')
        return redirect(url_for(index_url))
    except Exception as e:
        flash(str(e),'error')
        return redirect(request.referrer)


@bp_admin.route('/_delete_data',methods=["POST"])
@cross_origin()
def delete_data():
    table = request.json['table']
    data = request.json['ids']
    try:
        if not data:
            resp = jsonify(result=2)
            resp.headers.add('Access-Control-Allow-Origin', '*')
            resp.status_code = 200
            return resp

        for idx in data:
            query = "DELETE from {} where id = {}".format(table,idx)
            db.engine.execute(text(query))

        resp = jsonify(result=1)
        resp.headers.add('Access-Control-Allow-Origin', '*')
        resp.status_code = 200
        flash('Successfully deleted!','success')
        return resp
    except Exception as e:
        flash(str(e),'error')
        db.session.rollback()
        resp = jsonify(result=0)
        resp.headers.add('Access-Control-Allow-Origin', '*')
        resp.status_code = 200
        return resp
    

@bp_admin.route('/_get_view_modal_data',methods=["POST"])
@cross_origin()
def get_view_modal_data():
    try:
        table,column,id = request.json['table'],request.json['column'],request.json['id']
        query = "select {} from {} where id = {} limit 1".format(column,table,id)
        sql = text(query)
        row = db.engine.execute(sql)
        res = [x[0] if x[0] is not None else '' for x in row]
        
        print(res)
        """ For PO if editable """

        if table == 'purchase_order':
            resp = jsonify(result=str(res[0]),column=column,editable=False)
        else:
            resp = jsonify(result=str(res[0]),column=column)
        resp.headers.add('Access-Control-Allow-Origin', '*')
        resp.status_code = 200
        return resp
    except Exception as e:
        resp = jsonify(result="")
        resp.headers.add('Access-Control-Allow-Origin', '*')
        resp.status_code = 200
        return resp


def admin_edit(form, update_url, oid,modal_form=False, action="admin/admin_edit_actions.html", \
    model=None,extra_modal=None , template="admin/admin_edit.html", kwargs=None):
    fields = []
    row_count = 0
    field_sizes = []

    for row in form.edit_fields():
        fields.append([])
        field_count = 0

        for field in row:

            if field.input_type == 'select':
                data = field.model.query.all()
                # TODO: Dapat rektang AdminField nalang iaappend sa fields hindi na dictionary
                fields[row_count].append(
                    {'name': field.name, 'label': field.label, 'type': field.input_type, 'data': data,
                     'value': field.data,'placeholder':field.placeholder,'required':field.required})
            else:
                fields[row_count].append({'name': field.name, 'label': field.label, 'type': field.input_type,
                                          'value': field.data,'placeholder':field.placeholder,'required':field.required,
                                          'readonly': field.readonly
                                          })
            field_count = field_count + 1

        if field_count <= 2:
            field_sizes.append(6)
        elif field_count >= 3:
            field_sizes.append(4)

        row_count = row_count + 1
    context['edit_model'] = {
        'fields': fields,
        'fields_sizes':field_sizes,
    }

    if model:
        model_name = model.__amname__
        context['create_modal']['title'] = model_name
        context['active'] = model_name
        delete_table = model.__tablename__

    query1 = HomeBestModel.query.filter_by(name=model_name).first()

    if query1:
        check_module = HomeBestModule.query.get(query1.module_id)
        context['module'] = check_module.name

    if kwargs is not None:
        if 'template' in kwargs:
            template = kwargs.get('template')

        if 'active' in kwargs:
            context['active'] = kwargs.get('active')
        
        if 'update_url' in kwargs:
            update_url = kwargs.get('update_url')

    return render_template(template, context=context, form=form, update_url=update_url,
                           oid=oid,modal_form=modal_form,edit_title=form.edit_title,delete_table=delete_table,
                           action=action,extra_modal=extra_modal,index_url=index_url,title=form.edit_title,rendered_model=model)


def admin_index(*model, fields, form=None, url='', action="admin/admin_actions.html",
                create_modal="admin/admin_create_modal.html", view_modal="admin/admin_view_modal.html",
                create_url="", edit_url="", template="admin/admin_index.html",kwargs=None):
    
    model_name = model[0].__amname__
    if _check_read(model_name):
        if kwargs is not None and 'models' in kwargs:
            models = kwargs.get('models')
        else:
            if len(model) == 1:
                models = model[0].query.with_entities(*fields).all()
            elif len(model) == 2:
                models = model[0].query.outerjoin(model[1]).with_entities(*fields).all()
            elif len(model) == 3:
                query1 = db.session.query(model[0],model[1],model[2])
                models = query1.outerjoin(model[1]).outerjoin(model[2]).with_entities(*fields).all()

        # TODO: check if Admin.model_name is implemented in the model
        # Raise error if not

        context['create_modal']['title'] = model_name
        context['active'] = model_name
        context['model'] = model_name
        query1 = HomeBestModel.query.filter_by(name=model_name).first()
        if query1:
            check_module = HomeBestModule.query.get(query1.module_id)
            context['module'] = check_module.name

        table = model[0].__tablename__

        global index_url
        index_url = url

        if kwargs is not None:
            if 'template' in kwargs:
                template = kwargs.get('template')
            
            if 'active' in kwargs:
                context['active'] = kwargs.get('active')
            
            if 'edit_url' in kwargs:
                edit_url = kwargs.get('edit_url')
            
            if 'create_url' in kwargs:
                create_url = kwargs.get('create_url')

            # THIS IS FOR BOOLEAN WORD CONVERSION
            # if 'convert_boolean' in kwargs:
            #     if kwargs.get('convert_boolean') == 2:
            #         for model in models:
            #             for data in model:
            #                 if data == True:
            #                     data = 'YES'
            #                 else:
            #                     data = 'NO'

        if form is not None:
            table_fields = form.index_headers
            title = form.title
            index_title = form.index_title
            index_message = form.index_message

            if create_url and create_modal:
                _set_modal(create_url, form)
            elif create_modal:
                _set_modal('', form)

        else:
            
            if 'index_headers' not in kwargs:
                raise NotImplementedError('Must implement index_headers')
            else:
                table_fields = kwargs.get('index_headers')
            if 'index_title' not in kwargs:
                raise NotImplementedError("Must implement index_title")
            else:
                index_title = kwargs.get('index_title')
                title = index_title
            if 'index_message' not in kwargs:
                raise NotImplementedError("Must implement index_message")
            else:
                index_message = kwargs.get('index_message')

        return render_template(template, context=context,
                            models=models, table_fields=table_fields,
                            index_title=index_title, index_message=index_message,
                            title=title, action=action, create_modal=create_modal,
                            view_modal=view_modal, edit_url=edit_url,table=table,rendered_model=model[0])
    else:
        return render_template('auth/authorization_error.html',context=context)


def _check_read(model_name):
    from app.auth.models import User

    if current_user.is_superuser:
        return True
    else:
        user = User.query.get(current_user.id)
        for perm in user.permissions:
            if model_name == perm.model.name:
                if perm.read:
                    return True
                else:
                    return False
        return False

def _set_modal(url, form):
    fields = []
    row_count = 0
    field_sizes = []
    js_fields = []
    for row in form.create_fields():
        fields.append([])
        field_count = 0
        for field in row:
            if field.input_type == 'select':
                data = field.model.query.all()
                # TODO: Dapat rektang AdminField nalang iaappend sa fields hindi na dictionary
                fields[row_count].append(
                    {
                        'name': field.name, 'label': field.label, 'type': field.input_type, 
                        'data': data,'placeholder':field.placeholder,'required':field.required,'readonly':field.readonly,
                        'auto_generated': field.auto_generated
                        })
            else:
                fields[row_count].append(
                    {
                        'name': field.name, 'label': field.label, 'type': field.input_type,
                        'placeholder':field.placeholder,'required':field.required,'readonly':field.readonly,
                        'auto_generated': field.auto_generated
                        })
            field_count = field_count + 1
            js_fields.append(field.name)
        if field_count <= 2:
            field_sizes.append(6)
        elif field_count >= 3:
            field_sizes.append(4)
        row_count = row_count + 1
    context['create_modal'] = {
        'create_url': url,
        'create_form': form,
        'fields': fields,
        'fields_sizes':field_sizes,
        'js_fields':js_fields
    }


def admin_dashboard(box1=None,box2=None,box3=None,box4=None):
    from app.auth.models import User
    if not box1:
        box1 = DashboardBox("Total Modules","Installed",HomeBestModule.query.count())

    if not box2:
        box2 = DashboardBox("System Models","Total models",HomeBestModel.query.count())

    if not box3:
        box3 = DashboardBox("Users","Total users",User.query.count())
    
    context['active'] = 'main_dashboard'

    return render_template("admin/admin_dashboard.html", context=context,title='Admin Dashboard', \
        box1=box1,box2=box2,box3=box3)


class DashboardBox:
    def __init__(self,heading,subheading, number):
        self.heading = heading
        self.subheading = subheading
        self.number = number