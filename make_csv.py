import os
import patsy
import pandas as pd

def ser_types(ser):
    res = list(set(ser.apply(lambda x: str(type(x)))))
    return res

def df_coltypes(df):
    panda_types = pd.DataFrame(df.dtypes, columns=["PandaType"])
    python_types = pd.DataFrame(df.apply(ser_types), columns=["PythonTypes"])
    res = pd.merge(panda_types, python_types, how="outer",
             left_index=True, right_index=True)
    return res

data = patsy.demo_data('city', 'state', 'population', 'xLocation', 'yLatitude',
                       min_rows=100)
df = pd.DataFrame(data)
x = df_coltypes(df)

dir = os.path.expanduser("~")
fpath = os.path.join(dir, "sample.csv")
df.to_csv(fpath)
print ("done")
pass