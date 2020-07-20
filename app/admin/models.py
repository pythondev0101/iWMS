""" ADMIN MODELS"""
from app import db


class Admin(object):
    functions = [{}]
    model_description = ""
    
    @property
    def model_name(self):
        raise NotImplementedError('Must implement model_name')

    @property
    def model_icon(self):
        raise NotImplementedError('Must implement model_icon')


class AdminOptions(db.Model):
    __tablename__ = 'admin_options'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('auth_user.id'))
    header_color = db.Column(db.String(64))
    sidebar_color = db.Column(db.String(64))
