""" MODULE: AUTH.FORMS"""
""" FLASK IMPORTS """
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from datetime import datetime
"""--------------END--------------"""

from app.admin.forms import AdminIndexForm,AdminEditForm, AdminInlineForm, AdminField
from .models import Role
from app.iwms.models import Warehouse,Department,Group

class PermissionInlineForm(AdminInlineForm):
    headers =['Model','Read','create','write','delete']
    title = "Edit Rights"
    html = 'auth/permission_inline.html'

class ModelInlineForm(AdminInlineForm):
    headers = ['Model','Read','create','write','delete','add']
    title = "Add Rights"
    html = 'auth/model_inline.html'


# TODO: FOR FUTURE VERSION CHANGE THIS TO CLASS INHERITANCE
class UserEditForm(AdminEditForm):
    username = AdminField(label='Username', validators=[DataRequired()])
    email = AdminField(label='Email', input_type='email',required=False)
    fname = AdminField(label='First Name', validators=[DataRequired()])
    lname = AdminField(label='Last Name', validators=[DataRequired()])
    default_warehouse_id = AdminField(label='Default Warehouse',required=False,input_type='number',model=Warehouse)
    other_warehouse_id = AdminField(label='Other Warehouse',required=False,input_type='number',model=Warehouse)
    department_id = AdminField(label='Department',required=False,input_type='number',model=Department)
    group_id = AdminField(label='User Group',input_type='number',required=False,model=Group)
    def edit_fields(self):
        return [
            [self.fname, self.lname],
            [self.username,self.email],
            [self.default_warehouse_id,self.other_warehouse_id],[self.department_id,self.group_id]
            ]

    edit_title = "Edit User"
    edit_message = "message"

    permission_inline = PermissionInlineForm()
    # model_inline = ModelInlineForm()
    # inlines = [permission_inline,model_inline]
    inlines = [permission_inline]

class UserForm(AdminIndexForm):
    username = AdminField(label='Username', validators=[DataRequired()])
    email = AdminField(label='Email', input_type='email',required=False)
    fname = AdminField(label='First Name', validators=[DataRequired()])
    lname = AdminField(label='Last Name', validators=[DataRequired()])
    default_warehouse_id = AdminField(label='Default Warehouse',required=False,input_type='number',model=Warehouse)
    other_warehouse_id = AdminField(label='Other Warehouse',required=False,input_type='number',model=Warehouse)
    department_id = AdminField(label='Department',required=False,input_type='number',model=Department)
    group_id = AdminField(label='User Group',input_type='number',required=False,model=Group)
    def create_fields(self):
        return [
            [self.fname, self.lname],[self.username,self.email],
            [self.default_warehouse_id,self.other_warehouse_id],[self.department_id,self.group_id]]

    index_headers = ['Username','Warehouse', 'email','User group']
    index_title = "Users"
    index_message = "Message"


class UserPermissionForm(AdminIndexForm):
    index_headers = ['Username', 'Name', 'Model', 'Read','create', 'Write', 'Delete']
    index_title = "User Permissions"
    index_message = "Message"


class RoleModelInlineForm(AdminInlineForm):
    headers = ['Model','Read','create','write','delete']
    title = "Add role permissions"


class RoleCreateForm(AdminIndexForm):
    index_headers = ['Role Name','Active']
    index_title = "Groups"
    index_message = "Groups of permissions"

    name = AdminField(label="Name",validators=[DataRequired()])

    def create_fields(self):
        return [[self.name]]

    inline = RoleModelInlineForm()

    inlines = [inline]


class RoleEditForm(AdminEditForm):
    name = AdminField(label="Name",validators=[DataRequired()])

    def edit_fields(self):
        return [[self.name]]

    edit_title = "Edit group"
    edit_message = "message"
    
    permission_inline = PermissionInlineForm()
    model_inline = ModelInlineForm()
    permission_inline.html = "auth/role_permission_inline.html"
    model_inline.html = 'auth/role_model_inline.html'
    inlines = [permission_inline,model_inline]


# AUTH.FORMS.LOGINFORM
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log in')