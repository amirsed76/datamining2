import pandas as pd
from pandas.core.frame import DataFrame
import numpy as np
from SqlManager import SqlManager


def drop_numerical_outliers(input_df ):
    """
    inputs: a data frame
    outputs: outliers data frame and clean data
    Description:
            for all numerical attribute if a row has a outlier data delete it and append to outlier data frame
            this function work with IQR method
    """
    outliers_index = set()
    for header in input_df.columns:
        print(header," checked")
        df = input_df[header]
        if df.dtype == "int64":
            mean=df.mean()
            Q1 = df.quantile(0.25)
            Q3 = df.quantile(0.75)
            IQR = Q3 - Q1
            if IQR == 0:
                #means capitals
                # 99999
                trueList = ~(df > 41311)
            else:
                trueList = ~((df < (Q1 - 1.5 * IQR)) | (df > (Q3 + 1.5 * IQR)))
            for index, is_ok in enumerate(trueList.values.tolist()):
                if not is_ok:
                    outliers_index.add(index)

    outliers_index = list(outliers_index)
    outliers_list = []
    main_list = []
    values = input_df.values
    for i in range(len(values)):
        if i in outliers_index:
            outliers_list.append(list(values[i]))
        else:
            main_list.append(list(values[i]))
    outliers_df = DataFrame(outliers_list,
                            columns=['age', 'workclass', 'education_num', 'marital_status', 'post',
                                     'relationship', 'nation', 'gender', 'capital_gain', 'capital_loss',
                                     'hours_per_week',
                                     'country', 'wealth'])

    main_df = DataFrame(main_list,
                        columns=['age', 'workclass', 'education_num', 'marital_status', 'post',
                                 'relationship', 'nation', 'gender', 'capital_gain', 'capital_loss', 'hours_per_week',
                                 'country', 'wealth'])

    return outliers_df, main_df


def pre_processing(df: DataFrame):
    """
    input : a data frame
    outputs: clean data frame
            dtype.txt : a file that has type of each columns
            database:information.sqlite
            tables:
                 information  : clean data frame
                 before_process : data before process
                 missing_information : information of missing_data function output
                 outliers : outliers data
                 describe : describe of clean data

    Description:
                delete null information
                merge capital_gain and capital_loss
                delete education column
                delete outlier information with IQR method
                save information in database

    """
    sql_manager = SqlManager("information.sqlite")
    df.to_sql(name="before_process", con=sql_manager.conn, if_exists="replace")
    df.replace('?', np.NaN, inplace=True)
    missing_data_df = missing_data(df)
    missing_data_df.to_sql(name="missing_information", con=sql_manager.conn, if_exists="replace")
    main_df = df.dropna()
    print(main_df.shape)
    main_df = main_df.drop(columns=['education',"fnlwgt"])
    outliers_df, main_df = drop_numerical_outliers(main_df)
    main_df["capital"] = main_df["capital_gain"] - main_df["capital_loss"]
    main_df = main_df.drop(columns=["capital_gain", "capital_loss" ])
    main_df = main_df[['age', 'workclass', 'education_num', 'marital_status', 'post',
                       'relationship', 'nation', 'gender', 'capital', 'hours_per_week',
                       'country', 'wealth']]
    outliers_df.to_sql(name="outliers", con=SqlManager("information.sqlite").conn, if_exists="replace", index=False)
    main_df.to_sql(name="information", con=SqlManager("information.sqlite").conn, if_exists="replace", index=False)
    print(main_df.shape)
    main_df.describe().to_sql(name="describe", con=sql_manager.conn, if_exists='replace')
    with open("outs\\dtypes.txt", "w") as file:
        file.write(str(main_df.dtypes))
    return main_df


def missing_data(data):
    """
        information of missing data
    """
    total = data.isnull().sum()
    percent = (data.isnull().sum() / data.isnull().count() * 100)
    tt = pd.concat([total, percent], axis=1, keys=['Total', 'Percent'])
    types = []
    for col in data.columns:
        dtype = str(data[col].dtype)
        types.append(dtype)
    tt['Types'] = types
    return np.transpose(tt)


if __name__ == '__main__':
    csv_file = "fout.csv"
    df = pd.read_csv(csv_file,
                     names=['age', 'workclass', 'fnlwgt', 'education', 'education_num', 'marital_status', 'post',
                            'relationship', 'nation', 'gender', 'capital_gain', 'capital_loss', 'hours_per_week',
                            'country', 'wealth'], skipinitialspace=True)
    df = pre_processing(df=df)
