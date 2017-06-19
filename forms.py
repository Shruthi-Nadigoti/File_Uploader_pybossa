
from flask_wtf import Form
from flask_wtf.file import FileField, FileRequired
from wtforms import IntegerField,validators
from wtforms.widgets import HiddenInput
from flask.ext.babel import lazy_gettext
from flask.ext.wtf import Form, widgets
#import validator as pb_validator

class TaskUpload(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    avatar = FileField(lazy_gettext('Avatar'), validators=[FileRequired()])
from flask import Flask, render_template
from flask.ext.wtf import Form, widgets

SECRET_KEY = 'development'

app = Flask(__name__)
app.config.from_object(__name__)

"""class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class SimpleForm(Form):
    string_of_files = ['one\r\ntwo\r\nthree\r\n']
    list_of_files = string_of_files[0].split()
    # create a list of value/description tuples
    files = [(x, x) for x in list_of_files]
    example = MultiCheckboxField('Label', choices=files)"""
