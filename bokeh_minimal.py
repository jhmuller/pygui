
import os
import psutil
import sys
import logging
import re
import pandas as pd
import numpy as np
import datetime
import inspect
import copy
import patsy
from bokeh.layouts import row, column, widgetbox, Spacer
from bokeh.models.widgets.markups import Paragraph
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, CustomJS
from bokeh.models.tools import HoverTool, WheelZoomTool
from bokeh.models.widgets import Button, RadioButtonGroup
from bokeh.models.widgets import Slider, Select, DataTable, TableColumn, NumberFormatter

from bokeh.models.widgets.inputs import  TextInput
from bokeh.models.widgets import Button
from bokeh.client import push_session
import bokeh.io as bio
from bokeh.document import Document
from os.path import expanduser
import bokeh_utils as bu

mod_fpath = os.path.abspath(__file__)
mod_fname = os.path.split(mod_fpath)[1]
mod_fbase = os.path.splitext(mod_fname)[0]

CloseButton = Button(label="Close")
TextBox = TextInput()
MessageBox = Paragraph(text='hello')

def close_session():
    global session
    session.close()
    TheDoc.clear()
    #TheDoc.delete_modules()
    print ("Done")

close_browser_js = CustomJS(code="""
        var w = window ;
        console.log(w);
        alert("Stop") ;
        close() ;
        alert("Here") ;
        window.close() ;

    """)

def update_textbox(attr, old, new):
    MessageBox.text = new
    return

#CloseButton.on_click(close_session)
CloseButton.callback = close_browser_js
TextBox.on_change("value", update_textbox)
def set_message(text):
    global MessageBox
    MessageBox.text = text

layout = column(MessageBox,
                TextBox,
                CloseButton)

oldcurdoc = bio.curdoc()
currentstate = bio.curstate()
TheDoc = Document(title="NewDoc")
TheDoc.add_root(layout)



def get_function_name(stackpos=1):
    '''  call me to get your name
    :return: name of the calling function
    '''
# my_name = inspect.stack()[0][3]
    caller = inspect.stack()[stackpos][3]
    return caller

def session_update():
    msg = get_function_name()
    msg += "\n%s" % (session.id,)
    msg += str(TheDoc)
    if False:
        msg += session_diagnostics(session)
    logger = logging.getLogger(__name__)
    logger.info(msg)
    return

def doc_diagnostics(doc):
    js = doc.to_json_string(indent=2)
    return js

def session_diagnostics(session):
    djs = session.document.to_json_string()
    msg = djs
    msg += ''
    sid = session.id
    msg += "Session_id = %s" % (sid,)
    si_map = session.request_server_info()
    print ('a')
    for k, v in si_map.items():
        msg += "\n%s: %s" % (str(k), str(v))
    logger = logging.getLogger(__name__)
    logger.info(msg)
    from bokeh.util.browser import get_browser_controller

    #controller.close(server_url + "?bokeh-session-id=" + _encode_query_param(session.id))


def on_server_loaded(server_context):
    ''' If present, this function is called when the server first starts. '''
    print( "server loaded")
    pass

def on_server_unloaded(server_context):
    ''' If present, this function is called when the server shuts down. '''
    pass

def on_session_created(session_context):
    ''' If present, this function is called when a session is created. '''
    print( "Session Created")
    pass

def on_session_destroyed(session_context):
    ''' If present, this function is called when a session is closed. '''
    print ("Session Destroyed")
    pass


def main(fpath):
    global session

    session = push_session(TheDoc)
    message = fpath
    set_message(text=message)

    TheDoc.add_periodic_callback(session_update, 2000)
    session.show(layout)
    res = session_diagnostics(session)
    session.loop_until_closed()

if __name__ == "__main__":
    session = None
    main(sys.argv[1:])

