
import os
import psutil
import sys
import logging
import re
import pandas as pd
import numpy as np
import datetime
import inspect
from concurrent.futures import ProcessPoolExecutor
import copy
import patsy
from bokeh.layouts import row, column, widgetbox, Spacer
from bokeh.models.widgets.markups import Paragraph
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, CustomJS
from bokeh.models.tools import HoverTool, WheelZoomTool
from bokeh.models.widgets import Button, RadioButtonGroup
from bokeh.models.widgets import Slider, Select, DataTable, TableColumn, NumberFormatter
from bokeh.io import curdoc
from bokeh.models.widgets.inputs import  TextInput
from bokeh.models.widgets import Button
from bokeh.client import push_session
from os.path import expanduser
import bokeh_utils as bu
import bokeh.io as bio
from bokeh.document import Document

mod_fpath = os.path.abspath(__file__)
mod_fname = os.path.split(mod_fpath)[1]
mod_fbase = os.path.splitext(mod_fname)[0]


MetaSource = ColumnDataSource()
MetaSource.name = "Meta"
MetaTable = bu.data_table(source=MetaSource,
                            width=600)
MetaTable.name = "MetaTable"

ChosenSource = ColumnDataSource()
ChosenSource.name = "ChosenSource"
ChosenTable = bu.data_table(source=ChosenSource,
                            width=900)
ChosenTable.name = "ChosenTable"
MessageBox = Paragraph(text="Go")
layout = column(MessageBox,
                column(bu.child_in_widgetbox(MetaTable),
                    bu.child_in_widgetbox(ChosenTable)),)

oldcurdoc = bio.curdoc()
currentstate = bio.curstate()
TheDoc = Document(title="NewDoc")
TheDoc.add_root(layout)


def setup_chosen(fpath):

    try:
        df = pd.DataFrame.from_csv(fpath)
    except Exception as exc:
        msg = str(exc)
        MessageBos.text = msg
    bu.update_source_data(dom=layout,
                          source=ChosenSource, df=df)
    bu.update_table_source(dom=layout, table=ChosenTable, width=900)
    df = bu.df_summary(df)
    bu.update_source_data(dom=layout, source=MetaSource, df=df)
    bu.update_table_source(dom=layout, table=MetaTable, width=600)

FilePath = None
session = None
def setup(fpath=None):
    global session
    global FilePath
    FilePath = fpath
    #TheDoc.title = str(fpath)
    session = push_session(TheDoc)
    message = fpath
    setup_chosen(fpath=fpath)

    TheDoc.add_periodic_callback(session_update, 2000)
    session.show(layout)
    res = session_diagnostics(session)
    session.loop_until_closed()

def get_function_name(stackpos=1):
    '''  call me to get your name
    :return: name of the calling function
    '''
# my_name = inspect.stack()[0][3]
    caller = inspect.stack()[stackpos][3]
    return caller

def session_update():
    d = curdoc()
    msg = get_function_name()
    msg += "\n%s" % (session.id,)
    msg += str(d)
    if False:
        msg += session_diagnostics(session)
    logger = logging.getLogger(__name__)
    logger.info(msg)
    Timer.text += "<p>" + str(datetime.datetime.now())

def go(vobj):
    print (vobj)
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
    
    from bokeh.settings import settings    
    browser = settings.browser(None)    
    controller = get_browser_controller(browser=browser)
    print (dir(controller))

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



if __name__ == "__main__":
    currentdoc = curdoc()
    session = push_session(curdoc())
    curdoc().add_periodic_callback(session_update, 2000)
    session.show(layout)
    res = session_diagnostics(session)
    from bokeh.util.browser import get_browser_controller
    session.loop_until_closed()