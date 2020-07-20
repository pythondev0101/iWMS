""" MODULE: AUTH.MODELS """
""" FLASK IMPORTS """
from flask_login import UserMixin

"""--------------END--------------"""

""" PYTHON IMPORTS """
from werkzeug.security import generate_password_hash, check_password_hash

"""--------------END--------------"""

""" APP IMPORTS  """
from app import login_manager,db
from app.admin.models import Admin
from app.core.models import Base
"""--------------END--------------"""


# AUTH.MODEL.USER
class User(UserMixin, Base, Admin):
    __tablename__ = 'auth_user'

    username = db.Column(db.String(64), nullable=False, index=True, unique=True)
    fname = db.Column(db.String(64), nullable=False, server_default="")
    lname = db.Column(db.String(64), nullable=False, server_default="")
    email = db.Column(db.String(64), nullable=True, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    image_path = db.Column(db.String(64), nullable=False)
    permissions = db.relationship('UserPermission', cascade='all,delete', backref="user")
    is_superuser = db.Column(db.Boolean,nullable=False, default="0")
    role_id = db.Column(db.Integer, db.ForeignKey('auth_role.id'),nullable=True)
    role = db.relationship('Role', cascade='all,delete', backref="userrole")
    group_id = db.Column(db.Integer,db.ForeignKey('iwms_group.id',ondelete="SET NULL"),nullable=True)
    group = db.relationship('Group',backref='users')
    default_warehouse_id = db.Column(db.Integer,db.ForeignKey('iwms_warehouse.id',ondelete="SET NULL"),nullable=True)
    default_warehouse = db.relationship('Warehouse',foreign_keys=[default_warehouse_id])
    other_warehouse_id = db.Column(db.Integer,db.ForeignKey('iwms_warehouse.id',ondelete="SET NULL"),nullable=True)
    other_warehouse = db.relationship('Warehouse',foreign_keys=[other_warehouse_id])
    department_id = db.Column(db.Integer,db.ForeignKey('iwms_department.id',ondelete="SET NULL"),nullable=True)
    department = db.relationship('Department',backref='user')
    logs = db.relationship('CoreLog',backref='user_logs')

    def __init__(self):
        Base.__init__(self)
        self.image_path = "img/user_default_image.png"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return "<User {}>".format(self.username)

    model_name = 'Users'
    model_icon = 'pe-7s-users'
    model_description = "USERS"
    functions = [{'View users': 'bp_auth.index'},{'View roles': 'bp_auth.roles'}]


class UserPermission(db.Model):
    __tablename__ = 'auth_user_permission'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('auth_user.id', ondelete='CASCADE'))
    model_id = db.Column(db.Integer, db.ForeignKey('core_model.id'))
    model = db.relationship('HomeBestModel', backref="userpermission")
    read = db.Column(db.Boolean, nullable=False, default="1")
    create = db.Column(db.Boolean, nullable=False, default="0")
    write = db.Column(db.Boolean, nullable=False, default="0")
    delete = db.Column(db.Boolean, nullable=False, default="0")


class Role(Base):
    __tablename__ = 'auth_role'
    name = db.Column(db.String(64), nullable=False)
    role_permissions = db.relationship('RolePermission', cascade='all,delete', backref="role")
    model_name = 'Roles'
    model_icon = 'pe-7s-users'
    model_description = "Roles"

class RolePermission(db.Model):
    __tablename__ = 'auth_role_permission'
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('auth_role.id',ondelete='CASCADE'))
    model_id = db.Column(db.Integer, db.ForeignKey('core_model.id'))
    model = db.relationship('HomeBestModel', cascade='all,delete', backref="rolepermission")
    read = db.Column(db.Boolean, nullable=False, default="1")
    create = db.Column(db.Boolean, nullable=False, default="0")
    write = db.Column(db.Boolean, nullable=False, default="0")
    delete = db.Column(db.Boolean, nullable=False, default="0")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)