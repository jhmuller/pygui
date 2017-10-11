
import os
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
from bokeh.models.widgets import Slider, DataTable, TableColumn
from bokeh.io import curdoc
from bokeh.models.widgets import Button
from bokeh.client import push_session
from os.path import expanduser
import bokeh_utils as bu
import frame_analyzer as fa


mod_fpath = os.path.abspath(__file__)
mod_fname = os.path.split(mod_fpath)[1]
mod_fbase = os.path.splitext(mod_fname)[0]

CurDir = expanduser("~")

ProcPool = ProcessPoolExecutor()

def list_curdir():
    res = os.listdir(CurDir)
    return res


def update_curdir(newpath):
    global CurDir
    global MessageBox
    global Here
    MessageBox.text =  "<%s> to <%s>" % (CurDir,
                                          newpath,)
    if os.path.isdir(newpath):
        oldpath = copy.copy(CurDir)
        CurDir = newpath
        msg = dir_ok(thedir=CurDir)
        if msg == '':
            update_files_source()
            update_dirs_source()
            update_button_group(CurDir)
            Here.text = CurDir
        else:
            CurDir = oldpath
            msg += "Resetting to %s" % (CurDir,)
            MessageBox.text += msg
            return False
    else:
        msg = "<%s> not a dir" % (newpath,)
        MessageBox.text += msg
        return False
    return True

def dir_ok(thedir):
    try:
        dirs = bu.dirs_in_dir(thedir=thedir)
        files = bu.files_in_dir(thedir=thedir)
    except Exception as exc:
        print(exc)
        msg = str(exc)
        return msg
    else:
        if len(files) + len(dirs) == 0:
            msg = "No files in %s" % (thedir,)
            return msg
        else:
            return ''

def update_dirs_source():
    dirs_source.data = dict(Name=bu.dirs_in_dir(thedir=CurDir))
    dirs_source.selected = {'0d': {'glyph': None, 'indices': []},
                                '1d': {'indices': []}, '2d': {}}
    return


def update_files_source():
    files = bu.files_in_dir(thedir=CurDir)
    data = dict(Name=files)
    files_source.data = data
    return

def update_button_group(path):
    lst = bu.list_from_path(path)
    button_group.labels=lst
    button_group.active=None


def dir_select(new):
    if new is None:
        print ("Here")
        return
    lst = button_group.labels
    if len(lst) < new+1:
        msg = "lst too short"
        print (msg)
    newpath = bu.path_from_list(lst[:(new+1)])
    ok = update_curdir(newpath)
    if ok:
        button_group.labels = button_group.labels[:(new+1)]
    return

def file_select(attr, old, new):
    fdir = bu.path_from_list(button_group.labels)
    files = bu.get_source_selected_dict(files_source)
    csvfiles = [f for f in files
               if re.search(".csv", f) is not None]
    if len(csvfiles) == 0:
        msg = "No csv files chosen"
        MessageBox.text = msg
        return
    fpath = os.path.join(fdir, csvfiles[0])



cfg = bu.config()
Config = Paragraph(text=bu.config())
Above = Paragraph(text="You are Here")
Here = Paragraph()
Here.text = CurDir
MessageBox = Paragraph(text="Go")
Timer = Paragraph()
spacer = Paragraph(width=10)
blabels = bu.list_from_path(CurDir)
button_group = RadioButtonGroup(labels=blabels)
button_group.on_click(dir_select)

def dirs_source_callback(attr, old, new):
    global dirs_source
    oldind = old.get('1d', None)
    newind = (new['1d']['indices'][0]
              if len(new['1d']['indices']) > 0
              else None)
    if newind is None:
        return
    if dirs_source.data['Name'][newind] == '.':
        return
    newpath = (dirs_source.data['Name'][newind]
              if newind is not None
              else None)

    newpath = os.path.join(CurDir, newpath)
    update_curdir(newpath)
    dirs_source.selected = {'0d': {'glyph': None, 'indices': []},
                                '1d': {'indices': []}, '2d': {}}
    dirs_source.select(None)
    return


dirs_source = ColumnDataSource()
data = dict(Name=bu.dirs_in_dir(thedir=CurDir))
dirs_source.data = data
dir_table = bu.data_table(source=dirs_source,
                         titlemap={"Name":"Dirs"},
                          width=150)

files_source = ColumnDataSource()
files_source.name = 'Files'
files_source.data = dict(Name=bu.files_in_dir(thedir=CurDir))
files_table = bu.data_table(source=files_source,
                            titlemap={"Name":"Files"},
                            width=200)

dirs_source.on_change("selected", dirs_source_callback)

def update_chosen(attr, old, new):
    selected = bu.get_sources_selected_dict([files_source,])
    fname =  (selected['Files']['Name'])
    if re.search(".csv$", fname) is None:
        return
    fpath = os.path.join(CurDir, fname)
    if not os.path.isfile(fpath):
        return
    try:
        df = pd.DataFrame.from_csv(fpath)
    except Exception as exc:
        msg = str(exc)
        MessageBox.text = msg
    kwargs = dict(fpath=fpath)
    #fa.setup(fpath=fpath)
    ProcPool.submit(fa.setup, **kwargs)
    MessageBox.text = "We're back"


files_source.on_change("selected", update_chosen)


layout = column(row(Config),
                Above, Here,
                button_group,
                row(bu.child_in_widgetbox(dir_table),
                    bu.child_in_widgetbox(files_table)),
                MessageBox,
             )

curdoc().add_root(layout)
curdoc().title = "FileChooser"


def get_function_name(stackpos=1):
    '''  call me to get your name
    :return: name of the calling function
    '''
# my_name = inspect.stack()[0][3]
    caller = inspect.stack()[stackpos][3]
    return caller

def session_update():
    global session
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


def on_session_destroyed(session_context):
    ''' If present, this function is called when a session is closed. '''
    print ("Session Destroyed")


if __name__ == "__main__":
    currentdoc = curdoc()
    session = push_session(curdoc())
    curdoc().add_periodic_callback(session_update, 2000)
    session.show(layout)
    session_diagnostics(session)
    session.loop_until_closed()