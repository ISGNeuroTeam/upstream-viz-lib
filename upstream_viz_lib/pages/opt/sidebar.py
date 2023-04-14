import pandas as pd

def get_default_params(uploaded_file):
    """
    upstream-viz  pages/opt/sidebar.py 5
    Returns default economic parameters.
    Args:
        uploaded_file (str): path to csv file with predefined default parameters 

    Returns:
        Dict: dictionary with default parameters 
    """
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        return df.set_index("Переменная")["Значение"].to_dict()
    return {
        "perc": 99.994,
        "process_loss": 0.0002,
        "Netback": 16089,
        "Gor": 48.0,
        "Gasback": 619,
        "perc_g": 1.1,
        "tax_rate_MPT": 10158,
        "semi_fixed": 1000,
        "ratio_inj_pro": 1.1,
        "specific_energy_inj": 4.4,
        "specific_energy_tr_n": 0.03,
        "specific_energy_tr_zh": 1.1,
        "specific_energy_tr_v": 0.0,
        "specific_energy_tr_g": 4.4,
        "energy_cost": 2.2,
        "unit_costs_n": 0.0,
        "outgo_inj": 0.0,
        "outgo_prep": 0.0,
        "outgo_tr_g": 0.0,
        "revex_other": 0.0,
        "average_TBR": 500,
        "burning_fine_rate": 853.0,
        "burning_perc": 6.5,
        "CAPEX": 0.0,
    }

def get_params(default_params):
    """
    upstream-viz  pages/opt/sidebar.py 206
    Returns Economic parameters.
    Args:

    Returns:
        Dict: dictionary with parameters
    """    
    ret_params = default_params.copy()
    ret_params["ratio_inj_pro"] = 1.1
    ret_params["unit_costs_n"] = 0
    ret_params["average_TBR"] = 500
    return ret_params

def get_only_working():
    """
    upstream-viz  pages/opt/sidebar.py 206
    Do we need to show percent of loading only for work objects.
    Args:

    Returns:
        bool: Yes/No 
    """        
    return True

def get_only_changes():
    """
    upstream-viz  pages/opt/sidebar.py 206
    Show only recommendations?
    Args:

    Returns:
        bool: Yes/No 
    """    
    return False