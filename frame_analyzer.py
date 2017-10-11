
import os
import psutil
import sys
import logging
import re
import pandas as pd
import numpy as np
import datetime
import functools
import inspect
from concurrent.futures import ProcessPoolExecutor
from bokeh.layouts import row, column, widgetbox, Spacer
from bokeh.models.widgets.markups import Paragraph
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource
from bokeh.models.tools import HoverTool, WheelZoomTool
from bokeh.models.widgets import Button, Toggle, RadioButtonGroup, CheckboxButtonGroup
from bokeh.models.widgets import Select, TableColumn, NumberFormatter
from bokeh.io import curdoc
from bokeh.models.widgets.inputs import  TextInput
from bokeh.models.widgets import Button
from bokeh.plotting import Figure
from bokeh.client import push_session
from os.path import expanduser
import bokeh_utils as bu
import bokeh.io as bio
from bokeh.document import Document

mod_fpath = os.path.abspath(__file__)
mod_fname = os.path.split(mod_fpath)[1]
mod_fbase = os.path.splitext(mod_fname)[0]

def close_session():
    global session
    session.close()
    TheDoc.clear()
    #TheDoc.delete_modules()
    print ("Done")

MakeScatterPlot = Toggle(label="MakeScatter")

MessageBox = Paragraph(text="Go")
CloseButton = Button(label="Close")
CloseButton.on_click(close_session)
RowFilter = TextInput(value="")
ColumnChooser = CheckboxButtonGroup()

TheDoc = Document(title="NewDoc")
TheDoc.name = "TheDoc"


def setup(fpath=None):
    global session
    global FilePath
    FilePath = fpath
    TheDoc.title = str(fpath)
    session = push_session(TheDoc)

    layout = setup_chosen(fpath=fpath)
    TheDoc.add_root(layout)

    TheDoc.add_periodic_callback(session_update, 2000)
    session.show(layout)
    session_diagnostics(session)
    session.loop_until_closed()

def make_scatter(new, dom):
    MessageBox.text = str(new)
    Xselect = dom.select_one(dict(name='ScatterPlotX'))
    Yselect = dom.select_one(dict(name='ScatterPlotY'))
    ChosenSource = dom.select_one(dict(name='ChosenSource'))
    ssource = dom.select_one(dict(name='ScatterSource'))
    ssource.data = dict(X=ChosenSource.data[Xselect.value],
                              Y=ChosenSource.data[Yselect.value])

    


    print 'here'

def setup_chosen(fpath):
    try:
        df = pd.DataFrame.from_csv(fpath)
    except Exception as exc:
        msg = str(exc)
        MessageBox.text = msg
    dfcols = list(df.columns)

    ChosenSource = ColumnDataSource()
    ChosenSource.data = bu.column_data_source_data_from_df(df)
    ChosenSource.name = "ChosenSource"
    ChosenTable = bu.data_table(source=ChosenSource,
                                               columns=dfcols,
                                               width=800)
    ChosenTable.name = "ChosenTable"

    metadf = bu.df_summary(df)
    MetaSource = ColumnDataSource()
    MetaSource.name = "MetaSource"
    MetaSource.data = bu.column_data_source_data_from_df(metadf)
    MetaTable = bu.data_table(source=MetaSource,
                               columns=list(metadf.columns),
                                       width=600)
    MetaTable.name = "MetaTable"

    RowFilter.value = ("# enter row filter conditions here")
    ScatterPlotX = Select(options = dfcols,
                          value=dfcols[0])
    ScatterPlotX.name = 'ScatterPlotX'
    ScatterPlotY = Select(options = dfcols,
                          value=dfcols[-1])
    ScatterPlotY.name = 'ScatterPlotY'
    ScatterSource = ColumnDataSource()
    ScatterSource.name = 'ScatterSource'
    ScatterSource.data = dict(X=ChosenSource.data[ScatterPlotX.value],
                              Y=ChosenSource.data[ScatterPlotY.value])
    ScatterPlot = Figure(height=500, width=600)
    res = ScatterPlot.scatter(x='X',
                         y='Y',
                         source=ScatterSource)
    res.name = "srender"
    ScatterPlot.name = 'ScatterPlot'

    layout= column(MessageBox, CloseButton,
                RowFilter,
                ColumnChooser,
                column(bu.child_in_widgetbox(MetaTable),
                    bu.child_in_widgetbox(ChosenTable)),
                row(ScatterPlotX, ScatterPlotY, MakeScatterPlot),
                ScatterPlot,)
    MakeScatterPlot.on_click(functools.partial(make_scatter, dom=layout))
    currentstate = bio.curstate()

    return layout


FilePath = None
session = None

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
    #session.show(layout)
    session_diagnostics(session)
    session.loop_until_closed()