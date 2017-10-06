
import os
import psutil
import sys
import logging
import re
import pandas as pd
import datetime
import inspect
import db_helper as dbh
import patsy
from bokeh.layouts import row, column, widgetbox, Spacer
from bokeh.models.widgets.markups import Paragraph
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, CustomJS
from bokeh.models.tools import HoverTool, WheelZoomTool
from bokeh.models.widgets import Slider, Select, DataTable, TableColumn, NumberFormatter
from bokeh.io import curdoc
from bokeh.models.widgets.inputs import  TextInput
from bokeh.models.widgets import Button
from bokeh.client import push_session
from os.path import expanduser

Servers = ['Bos-DBResearch01']


def databases_on_server(server):
    dbs = dbh.get_all_databases_list(server)
    return dbs

def column_data_source_data_from_df(df,
                                    index_key=None):
    data = {}
    if index_key is not None:
        data[index_key] = df.index
    for c in df.columns:
        data[c] = df[c]
    return data

def source_data_from_df(df,
                        index_key=None):
    data = {}
    if index_key is not None:
        data[index_key] = df.index
    for c in df.columns:
        data[c] = df[c]
    return data

def source_data_from_list(lst, key):
    data = {key:lst}
    return data


def table_columns_from_source(source,
                              titlemap=None):
    titlemap = ({} if not isinstance(titlemap, dict)
                else titlemap)
    tcols = []
    for k, v in source.data.items():
        title = titlemap.get(k, k)
        tc = TableColumn(field=k, title=title)
        tcols.append(tc)
    return tcols

def data_table(source, titlemap=None, width=None):

    tcols = table_columns_from_source(source,
                                      titlemap=titlemap)
    kwargs = dict(source=source,
                  columns=tcols)
    if width is not None:
        kwargs['width'] = width
    res = DataTable(**kwargs)
    return res

def get_source_selected_indexes(source):
    inds = source.selected['1d']['indices']
    return inds

def get_source_selected_dict(source):
    inds = get_source_selected_indexes(source)
    ind = (0 if len(inds) == 0
           else inds[0])
    res = {}
    for key in source.data.keys():
        res[key] = source.data[key][ind]
    return res

def get_sources_selected_dict(sources):
    selected = {}
    for si, source in enumerate(sources):
        name = (source.name if hasattr(source, "name")
                else str(si))
        selected[name] = get_source_selected_dict(source)
    return selected

def update_tbl_source(attr, old, new):
    selected = get_sources_selected_dict([servers_source,
                                          server_dbs_source])
    df = dbh.get_all_tables_df(server=selected['server']['Name'],
                                  db_list=[selected['db']['Name']])
    tbls = df.table_name.values
    db_tables_source.data = {"Name":list(tbls)}
    return


def replace_layout_elem(name, new_elem):
    pass

def update_chosen_table(attr, old, new):
    selected = get_sources_selected_dict([servers_source,
                                          server_dbs_source,
                                          db_tables_source])
    qry = "Select top 100 * from %s" % (selected['table']['Name'])
    df = dbh.qry_via_pandas(qry,
                            server=selected['server']['Name'],
                            db=selected['db']['Name'],
                               )
    old_source = layout.select_one(dict(name='ChosenSource'))

    data = source_data_from_df(df)
    layout.set_select(selector=dict(name="ChosenSource"),
                      updates=dict(data=data))
    old_table = layout.select_one(dict(name='ChosenTable'))
    tcols = table_columns_from_source(old_source)
    layout.set_select(selector=dict(name="ChosenTable"),
                      updates=dict(columns=tcols,
                                   fit_columns=True,
                                   width=900))

    return


servers_source = ColumnDataSource()
servers_source.name = 'server'
servers_source.data = source_data_from_list(lst=Servers,
                                            key='Name',)
servers_table = data_table(source=servers_source,
                           titlemap={"Name":"Server"},
                           width=200)
init_dbs = databases_on_server(server=Servers[0])

server_dbs_source = ColumnDataSource()
server_dbs_source.name = 'db'
server_dbs_source.data = source_data_from_list(lst=init_dbs,
                                       key='Name',)
server_dbs_table = data_table(source=server_dbs_source,
                              titlemap={"Name":"Db"},
                              width=200)

server_dbs_source.on_change("selected", update_tbl_source)

db_tables_df = dbh.get_all_tables_df(server=Servers[0],
                                  db_list=init_dbs[:1])

init_tbls = db_tables_df.table_name.values
db_tables_source = ColumnDataSource()
db_tables_source.name = 'table'
db_tables_source.data = source_data_from_list(lst=init_tbls,
                                          key='Name',)
db_tables_table = data_table(source=db_tables_source,
                             titlemap={"Name":"Table"},
                             width=200)
db_tables_source.on_change("selected", update_chosen_table)

chosen_table_source = ColumnDataSource()
chosen_table_source.name = 'ChosenSource'
chosen_table_table = data_table(source=chosen_table_source,
                                width=800)
chosen_table_table.name = "ChosenTable"

MessageBox = Paragraph(text="Go")

def child_in_widgetbox(child, pad=50):
    args = [child]
    kwargs = ({} if child.width is None
              else {"width":child.width+pad})
    res = widgetbox(*args, **kwargs)
    return res

layout = column(
                row(child_in_widgetbox(servers_table),
                    child_in_widgetbox(server_dbs_table),
                    child_in_widgetbox(db_tables_table)),
                chosen_table_table,
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
    d = curdoc()
    msg = get_function_name()
    msg += "\n%s" % (session.id,)
    msg += str(d)
    if False:
        msg += session_diagnostics(session)
    logger = logging.getLogger(__name__)
    logger.info(msg)
    #Timer.text += "<p>" + str(datetime.datetime.now())

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
    import numpy as np
    sran = np.random.randint(1, 20000)
    session = push_session(curdoc())
    curdoc().add_periodic_callback(session_update, 2000)
    session.show(layout)
    res = session_diagnostics(session)
    session.loop_until_closed()