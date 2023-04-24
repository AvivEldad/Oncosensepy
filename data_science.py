import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import itertools
import validation as valid


def important_L(df, err_limit, threshold):
    """
        This method returns a DataFrame with only the important columns. An important column is determined
        by whether the number of cells whose value is higher in absolute value than the error limit,
        is greater than or equal to the threshold.

        Arguments:
            df (pandas.DataFrame): The DataFrame to be checked.
            err_limit (float): The error limit.
            threshold (int): The number of significant values.

        Returns:
            pandas.DataFrame: The DataFrame with only the important columns selected.
    """
    valid.is_valid_L(df)
    new_df = df.loc[:, :5].copy()
    new_df['time'] = new_df['time'].apply(lambda x: '0hr' if x == 0 else x)
    for i in range(1, len(df.columns) - 5):
        count = 0
        for cell in df[i]:
            if abs(cell) > err_limit:
                count += 1
        if count >= threshold:
            new_df[i] = df[i].copy()
    return new_df


def filter_by_col(df, col, filter_list):
    """
        This function filters data by a certain column and by a list of values it receives.

        Arguments:
            df (pandas.DataFrame): The DataFrame to filter.
            col (str): The column according to which the filtering will be performed.
            filter_list (List): A list of values that we would like to appear in the selected column.

        Returns:
            pandas.DataFrame: The DataFrame after filtering.
    """
    valid.is_valid_L(df)
    filter_df = df.loc[(df[col].isin(filter_list))]
    if len(filter_df) == 0:
        print(f"There is no data to show by '{col}' filtering")
    return filter_df


def plot_G_values(title, uid, values, path):
    """
        This function accepts columns representing processes and sorts for each process its proteins.
        In addition, the function saves the plot of process

        Arguments:
            title (str): The plot title.
            uid (list): The list of G_UID.
            values (list): The list of G_values.
            path (str): The path to save the figures, if None the plots will be displayed one by one
    """
    valid.is_valid_path(path)
    plt.title(title)
    plt.figure(figsize=(50, 30))
    plt.scatter(uid, values)
    plt.xticks(uid, [f'{name} ({i})' for i, name in enumerate(uid)], rotation=90, fontsize=6)
    plt.ylabel('Effect')

    for i, txt in enumerate(range(len(uid))):
        plt.text(uid[i], values[i] + 0.002, str(i), fontsize=5)

    plt.savefig(path + '/' + f'{title}.SVG', dpi=300)
    plt.close()


def sort_plot_G_values(g_df, cols, path=''):
    """
        This function accepts columns representing processes and sorts for each process its proteins.
        In addition, the function saves the plot of each process

        Arguments:
            g_df (pandas.DataFrame): The G_values DataFrame.
            cols (list): The process to sort it's G_values.
            path (str): The path to save the figures, if None the plots will be displayed one by one

        Returns:
            pandas.DataFrame: Sorted G_values.
    """
    if path == '':
        path = os.getcwd()
    valid.is_valid_path(path)
    important_g = pd.DataFrame(columns=pd.MultiIndex.from_product([cols, ['UID', 'Effect']]))
    names_g, values_g = {}, {}
    for col in important_g.columns:
        if col[1] == 'UID':
            names_g = g_df[col[1]].to_dict()
        else:
            values_g = g_df[col[0]].to_dict()
            sorted_values_g = dict(sorted(values_g.items(), key=lambda item: item[1]))
            list_values_g = list(sorted_values_g.values())

            sorted_names_g = dict(sorted(names_g.items(), key=lambda item: sorted_values_g[item[0]]))
            list_names_g = list(sorted_names_g.values())

            plot_G_values(f'Process {col[0]}', list_names_g, list_values_g, path)
            important_g[(col[0], 'UID')] = list_names_g
            important_g[col] = list_values_g

    return important_g


#             list_values_g contain lists, each one for proccess. for each of them, we need to divide for two,
# calculate the distance between each 2 points, and find the egdes


def pairs_df_to_dict(df, cell_name, control_list, inhibitor_list, fixed_col='time'):
    """
    Convert a Pandas dataframe to a dictionary of pairs of dataframes.

    Arguments:
        df (pandas.DataFrame): The input dataframe to convert.
        cell_name (str): The name of the cell line to filter the dataframe by.
        control_list (list): A list of control compound names.
        inhibitor_list (list): A list of inhibitor compound names.
        fixed_col (str): The name of the column that will remain fixed in each pair. Default is 'time'.

    Returns:
        dict: A dictionary where each key is a tuple representing a pair of compounds, along with optional time points.
              The corresponding value is a Pandas dataframe containing data for that pair.
              The keys are generated by combining cell_name, compound names and time points.
              There are two types of keys:
              (1) Keys for pairs of control_list and inhibitor_list with same fixed_col.
              (2) Keys for pairs of inhibitor_list with itself with different fixed_col.
    """
    # Filter the input dataframe to only include rows with the specified cell name
    df = df.loc[df['cell_line_name'] == cell_name]

    full_list = control_list + inhibitor_list

    # Filter the dataframe to only include rows with compound names in the full list
    df = df.loc[df['compound_name'].isin(full_list)]

    # If the filtered dataframe is empty, print an error message and exit the program
    if df.empty:
        print(f'There is a problem here: {control_list} or here: {inhibitor_list}')
        sys.exit()

    pairs_dict = {}
    # Pairs of control_list and inhibitor_list with same fixed_col
    for i, j in itertools.product(control_list, inhibitor_list):
        for col in df[fixed_col].unique():
            df_i_j_t = df.loc[(df['compound_name'] == i) & (df[fixed_col] == col)]
            df_j_i_t = df.loc[(df['compound_name'] == j) & (df[fixed_col] == col)]
            if not (df_i_j_t.empty or df_j_i_t.empty):
                pairs_dict[(cell_name, i, j, col)] = pd.concat([df_i_j_t, df_j_i_t])

    # Pairs of inhibitor_list with itself with different fixed_col
    for i in inhibitor_list:
        unique_fixed_col_i = df.loc[df['compound_name'] == i, fixed_col].unique()
        for t1, t2 in itertools.combinations(unique_fixed_col_i, 2):
            df_i_t1 = df.loc[(df['compound_name'] == i) & (df[fixed_col] == t1)]
            df_i_t2 = df.loc[(df['compound_name'] == i) & (df[fixed_col] == t2)]
            if not (df_i_t1.empty or df_i_t2.empty):
                pairs_dict[(cell_name, i, i, t1, t2)] = pd.concat([df_i_t1, df_i_t2])

    return pairs_dict


def analyze_pairs(pairs_dict, p_value=0.05):
    """
    This function analyzes pairs of compounds in a dictionary of Pandas dataframes.

    Arguments:
        pairs_dict (dict): A dictionary containing Pandas dataframes for each pair of compounds.
                           The keys of the dictionary are tuples of two compound names.
        p_value (float): The p-value threshold for determining whether the difference
                         between means is significant. Default is 0.05.

    Returns:
        dict: A dictionary with the same keys as the input dictionary, but with updated dataframes.
              If a key-value pair is removed from the dictionary because none of the columns pass the test,
              it will not appear in the output dictionary.
    """
    keys_to_remove = []
    for key, df in pairs_dict.items():
        col_names = df.columns.tolist()
        time_col_idx = col_names.index('time')
        analysis_cols = [c for c in col_names[time_col_idx + 1:]]

        dfs_to_concat = []
        for col in analysis_cols:
            df_first = df.loc[df['compound_name'] == key[1], col]
            df_second = df.loc[df['compound_name'] == key[2], col]

            first_avg = df_first.mean()
            second_avg = df_second.mean()

            if abs(first_avg - second_avg) > p_value:
                dfs_to_concat.append(df[[col]])

        if len(dfs_to_concat) == 0:
            keys_to_remove.append(key)
        else:
            new_df = pd.concat(dfs_to_concat, axis=1)
            new_df = new_df.reindex(sorted(new_df.columns), axis=1)
            pairs_dict[key] = pd.concat(
                [df[['barcode', 'cell_line_name', 'compound_name', '2D_3D', 'dosage', 'time']], new_df], axis=1)

    for key in keys_to_remove:
        pairs_dict.pop(key)

    # pd.set_option("display.max_rows", None)  # Display all rows
    # pd.set_option("display.max_columns", None)  # Display all columns
    # print(pairs_dict)


def create_pairs_df(pairs_dict):
    """
    This function takes a dictionary of paired DataFrames and concatenates them into a single DataFrame for comparison.

    Arguments:
        pairs_dict (dict): A dictionary of paired DataFrames.

    Returns:
        pandas.DataFrame: A concatenated DataFrame of paired DataFrames for comparison.
    """
    comp_list = []
    for i, df in enumerate(pairs_dict.values()):
        cols = df.columns.tolist()
        df = df.reindex(columns=cols)
        df.loc[-1] = cols
        df.index = df.index + 1
        df = df.sort_index()
        comp_list.append(df)
        if i < len(pairs_dict) - 1:
            comp_list.append(pd.DataFrame(np.nan, index=['-'], columns=df.columns))

    pairs_df = pd.concat(comp_list, sort=False)
    pairs_df = pairs_df.reset_index(drop=True)

    return pairs_df


def create_csv(df, name='default_name', path=None):
    """
        This method inserts the DataFrame into a csv file.

        Arguments:
            df (pandas.DataFrame): The DataFrame to insert into a new csv.
            name (str): File name.
            path (str): The file path.
    """
    if df.empty:
        print(f"The csv file '{name}' was not created because the DataFrame is empty")
        return

    # Create the folder if it doesn't exist
    elif path is None:
        folder = 'csv'
        if not os.path.exists(folder):
            os.makedirs(folder)
        path = folder + '/' + name + '.csv'  # Save the data frame to the CSV file
        df.to_csv(path)
    else:
        df.to_csv(path + '/' + name + '.csv')
    print(f"The csv '{name}' created successfully")


def create_new_sheet(df, path, sheet_name):
    """
        This method inserts the DataFrame into a new sheet in an existing Excel file.

        Arguments:
            df (pandas.DataFrame): The DataFrame to insert into a new sheet.
            path (str): The file path.
            sheet_name (str): The name of the new sheet.
    """
    if not df.empty:
        with pd.ExcelWriter(path, mode='a') as writer:
            df.to_excel(writer, sheet_name=sheet_name)
        print(f"The sheet '{sheet_name}' created successfully")
    else:
        print(f"The sheet '{sheet_name}' was not created because the DataFrame is empty")



def find_edges(g_df, cols):
    important_g = pd.DataFrame(columns=pd.MultiIndex.from_product([cols, ['UID', 'Effect']]))
    names_g, values_g = {}, {}
    for col in important_g.columns:
        if col[1] == 'UID':
            names_g = g_df[col[1]].to_dict()
        else:
            values_g = g_df[col[0]].to_dict()
            sorted_values_g = dict(sorted(values_g.items(), key=lambda item: item[1]))
            list_values_g = list(sorted_values_g.values())

            sorted_names_g = dict(sorted(names_g.items(), key=lambda item: sorted_values_g[item[0]]))
            list_names_g = list(sorted_names_g.values())

            #split the list into 2 lists
            half_ind = len(list_values_g) // 2
            first_half = list_values_g[:half_ind]
            second_half = list_values_g[half_ind:]
            distance, max = 0, 0
            first_indices, second_indices = [], []
            #find the max destination between 2 points and save their index and the value in first_indices
            for i in range(1, len(first_half)):
                distance = abs(abs(first_half[i]) - abs(first_half[i - 1]))
                if distance > max:
                    max = distance
                    first_indices = [i - 1, i , max]
            max = 0
            # find the max destination between 2 points and save their index and the value in second_indices
            for i in range(1, len(second_half)):
                distance = abs(abs(second_half[i]) - abs(second_half[i - 1]))
                if distance > max:
                    max = distance
                    second_indices = [i - 1, i, max]

            print(first_indices, second_indices)
            start_edge = list_names_g[: first_indices[1]]
            end_edge = list_names_g[half_ind + second_indices[0]:]
            print(start_edge)
            print(end_edge)
            print(("------------------------------------------------------"))