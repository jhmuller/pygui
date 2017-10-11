import os
import psutil
import sys
import logging
import re
import pandas as pd
import numpy as np
import datetime
import inspect
import patsy
from collections import OrderedDict
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


def config():
    login = None
    user = os.environ.get("USER", None)
    home = os.environ.get("HOME", None)
    try:
        login = os.getlogin()
    except Exception:
        pass
    res = "User: %s, " % (user,)
    res += "Home: %s, " % (home,)
    res += "Login: %s " % (login,)
    return res

def column_data_source_data_from_df(df,
                                    index_key=None):
    data = source_data_from_df(df)
    return data

def source_data_from_df(df,
                        index_key=None):
    data = OrderedDict()
    keys = list(df.columns)
    if index_key is not None:
        keys.insert(0, index_key)
        data[index_key] = df.index
    for i, key in enumerate(list(df.columns)):
        data[key] = df[key]
        print (i, key)
    return data    


def source_data_from_list(lst, key):
    data = {key:lst}
    return data


def column_width(lst):
    coltypes = list(set([str(type(x)) for x in lst]))
    coltype = (coltypes[0])
    if re.search("str|string", coltype) is not None:
        chlen = max([len(x) for x in lst])
    elif re.search("date", coltype) is not None:
        chlen = 14
    else:
        chlen = 10
    pixlen = chlen * 20
    return pixlen

def table_columns_from_source(source,
                              columns=None,
                              titlemap=None):
    titlemap = ({} if not isinstance(titlemap, dict)
                else titlemap)
    columns = (source.data.keys() if columns is None
               else columns)
    tcols = []
    for i, key in enumerate(columns):
        print (i, key)
        kwargs = dict(field = key,
                      title = titlemap.get(key, key),
                        width = column_width(source.data[key]))
        isfloat =  re.search("float", str(type(source.data[key][0])))
        if isfloat is not None:
            #kwargs['formatter'] = NumberFormatter(format="0,0.000")
            pass
        tc = TableColumn(**kwargs)
        tcols.append(tc),
    return tcols

def data_table(source,
               columns=None,
               titlemap=None,
               width=400,
               height=500,
               fit_columns=False):
    tcols = table_columns_from_source(source,
                                      columns=columns,
                                      titlemap=titlemap)
    kwargs = dict(source=source,
                  columns=tcols,
                  fit_columns=fit_columns)
    if width is not None:
        kwargs['width'] = width
    if height is not None:
        kwargs['height'] = height
    res = DataTable(**kwargs)
    return res

def get_source_selected_indexes(source):
    inds = source.selected['1d']['indices']
    return inds

def get_source_selected_dict(source):
    inds = get_source_selected_indexes(source)
    ind = (0 if len(inds) == 0
           else inds[0])
    selected = {}
    for key in source.data.keys():
        selected[key] = source.data[key][ind]
    return selected

def get_sources_selected_dict(sources):
    selected = {}
    for si, source in enumerate(sources):
        name = (source.name if hasattr(source, "name") and source.name is not None
                else str(si))
        selected[name] = get_source_selected_dict(source)
    return selected

def ser_types(ser):
    lst = list(set(ser.apply(lambda x: str(type(x)))))
    res = ','.join([str(e) for e in lst])
    return res

def panda_types(df):
    res = pd.DataFrame(df.dtypes, columns=["PandaType"])
    res['PandaType'] = [str(x) for x in res['PandaType']]
    res['Column'] = res.index
    return res

def python_types(df):
    res = pd.DataFrame(df.apply(ser_types), columns=["PyTypes"])
    res['PyTypesCnt'] = res['PyTypes'].apply(lambda x: len(x.split(',')))
    res['Column'] = res.index
    return res

def makelist(obj):
    res = obj
    res = ([] if res is None
           else res)    
    res = (res if isinstance(res, (list))
               else [res])

    return res

def reorder_df_columns(df,
                    atstart=None,
                    atend=None):
    atstart = makelist(atstart)
    atend = makelist(atend)
    inset = {}
    inset['atstart'] = set(atstart)
    inset['atend'] = set(atend)
    colset = set([str(c) for c in list(df.columns)])
    msg = ''
    for name, theset in inset.iteritems():
        if colset.intersection(theset) != theset:
            msg += "%s is not a subset of the columns " % (name,)
    if msg != '':
        raise ValueError(msg)
    if len(inset['atstart'].intersection(inset['atend'])) > 0:
        msg = "atstart and atend have overlap"
        raise ValueError(msg)
    middle = [c for c in df.columns
              if c not in inset['atstart']
              and c not in inset['atend']]
    res = df[atstart + middle + atend]
    return res



def generic_types(df):
    generic = {}
    generic['real'] = df.select_dtypes(include=[np.float])
    numeric = df.select_dtypes(include=[np.number])

    generic['int'] = [c for c in numeric
                      if c not in generic['real'] ]
    pytypes = python_types(df)
    generic['date'] = [c for c in df.columns if
                re.search('date|time', pytypes.ix[c]['PyTypes'], re.I) is not None]
    generic['string'] = [c for c in df.columns if
                re.search('str', pytypes.ix[c]['PyTypes'], re.I) is not None]
    res = pd.DataFrame(df.dtypes, columns=['x'])
    del res['x']
    res['GenericType'] = ''
    for k, lst in generic.iteritems():
        for c in lst:
            res.ix[c]['GenericType'] += str(k)
    res['Column'] = res.index
    res = reorder_df_columns(res, atstart='Column')
    return res

def apply_many(ser):
    funcmap = {'min': ser.min(),
               'max': ser.max(),
               'null' : sum(ser.isnull()),
               'notnull':  sum(ser.notnull()),
               'unique' : len(ser.unique()),
               }    
    
def df_stats(df):
    res = df.apply(lambda ser: pd.Series({'min': ser.min(),
                                        'max': ser.max(),
                                        'null' : sum(ser.isnull()),
                                        'notnull':  sum(ser.notnull()),
                                        'unique' : len(ser.unique()),
                                        })).transpose()
    datacols = list(res.columns)
    res['Column'] = res.index
    res = res[['Column'] + datacols]
    return res

def df_summary(df):
    pan = panda_types(df)
    py = python_types(df)
    temp = pd.merge(pan, py, how="outer",
                   on='Column',)

    gen = generic_types(df)
    temp = pd.merge(temp, gen, how='outer',
                   on='Column')

    stats = df_stats(df)
    res = pd.merge(temp, stats, how='outer',
                    on='Column')
    res = reorder_df_columns(res, atstart='Column')    
    return res


def update_source_data(dom, source, df):
        old_source = dom.select_one(dict(name=source.name))
        data = source_data_from_df(df.head(20))
        dom.set_select(selector=dict(name=source.name),
                          updates=dict(data=data),)

def update_table_source(dom,
                        table,
                        width=500,
                        height=None):
        old_table = dom.select_one(dict(name=table.name))
        tcols = table_columns_from_source(table.source)
        kwargs = dict(selector=dict(name=table.name),
                                    updates=dict(columns=tcols,
                                    fit_columns=False,
                                    width=width))
        if height is not None:
            kwargs['height'] = height
        dom.set_select(**kwargs)


def update_table_columns(dom,
                        table,
                        columns,
                        width=500,
                        height=None):
    old_table = dom.select_one(dict(name=table.name))
    tcols = table_columns_from_source(table.source,columns=columns)
    kwargs = dict(selector=dict(name=table.name),
                  updates=dict(columns=tcols,
                               fit_columns=False,
                               width=width))
    if height is not None:
        kwargs['height'] = height
    dom.set_select(**kwargs)

def list_from_path(path):
    plist = []
    while True:
        head, tail = os.path.split(path)
        if len(tail) == 0:
            plist.insert(0, head)
            break
        else:
            plist.insert(0,tail)
            path = head
    return plist

def items_in_dir(thedir, cfunc):
    items = os.listdir(thedir)
    res = [d for d in items
            if cfunc(os.path.join(thedir,d))]
    return res

def dirs_in_dir(thedir):
    res = items_in_dir(thedir=thedir,
                       cfunc=os.path.isdir)
    res = ['.']  + res
    return res

def child_in_widgetbox(child, pad=50):
    args = [child]
    kwargs = ({} if child.width is None
              else {"width":child.width+pad})
    res = widgetbox(*args, **kwargs)
    return res

def files_in_dir(thedir):
    res = items_in_dir(thedir=thedir,
                       cfunc=os.path.isfile)
    return res

def path_from_list(lst):
    path = lst[0]
    for elem in lst[1:]:
        path = os.path.join(path, elem)
    return path