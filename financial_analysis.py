import pandas as pd
import os
import csv
import numpy as np
import shutil



def build_panel(df, years):

    rows = []

    for _, row in df.iterrows():

        for year in years:

            new_row = {}

            # Kopiera metadata
            for col in static_columns:
                new_row[col] = row.get(col, np.nan)

            # Lägg till år
            new_row["year"] = year

            # Hämta årsdata
            for original_name, new_name in yearly_variables.items():

                column_name = f"{original_name} {year}"

                if column_name in df.columns:
                    new_row[new_name] = row[column_name]
                else:
                    new_row[new_name] = np.nan

            rows.append(new_row)

    return pd.DataFrame(rows)



def DELTA_total_assets(df):
    df["delta_total_assets"] = (
        df.groupby("Company name")["total_assets"].transform(lambda x: np.log(x / x.shift(1)))
        #.diff()
    )

    return df



def sale_growth(df):

    df["sale_growth"] = (
        df.groupby("Company name")["net_sales"]
        .transform(lambda x: np.log(x / x.shift(1)))
    )

    return df


def DELTA_sale_growth(df):

    df["delta_sale_growth"] = (
        df.groupby("Company name")["sale_growth"]
        .diff()
    )

    return df


def leverage(df):

    total_liabilities = (
        df["current_liabilities"] +
        df["long_term_liabilities"]
    )

    df["leverage"] = np.log(
        total_liabilities / df["total_assets"]
    )

    return df


def DELTA_leverage(df):

    df["delta_leverage"] = (
        df.groupby("Company name")["leverage"]
        .diff()
    )

    return df


def roa(df):

    assets_t = df["total_assets"]
    assets_t_1 = df.groupby("Company name")["total_assets"].shift(1)

    df["roa"] = (
        2 * df["ebit"] / (assets_t + assets_t_1)
    )

    return df


def DELTA_roa(df):

    df["delta_roa"] = (
        df.groupby("Company name")["roa"]
        .diff()
    )

    return df


def firm_age(df):

    def extract_year(x):
        if pd.isna(x):
            return np.nan

        try:
            return int(str(x)[:4])
        except:
            return np.nan

    formed_year = df["Formed date"].apply(extract_year)

    age = df["year"] - formed_year

    #df["firm_age"] = np.log(age.replace(0, np.nan))
    df["firm_age"] = np.log(age + 1) #avoid ln(0)

    return df



import numpy as np
import pandas as pd

def CEO_tenure(df):

    def extract_years(value):
        if pd.isna(value):
            return []

        parts = str(value).split("|")
        years = []

        for p in parts:
            p = p.strip()

            if p in ["", "-", "*"]:
                continue

            try:
                years.append(int(str(p)[:4]))
            except:
                continue

        return years

    # extrahera CEO-event en gång per rad (företag)
    df["__ceo_events__"] = (
        df["External CEO - Date appointed"].apply(extract_years) +
        df["CEO - Date appointed"].apply(extract_years)
    )

    def compute_tenure(row):
        year = row["year"]
        events = row["__ceo_events__"]

        valid = [e for e in events if e <= year]

        if len(valid) == 0:
            return np.nan

        last_event = max(valid)

        tenure = year - last_event

        #if tenure <=0:
        if tenure < 0:
            return np.nan

        #return np.log(tenure)
        return np.log(tenure + 1) #avoid ln(0)

    df["ceo_tenure"] = df.apply(compute_tenure, axis=1)

    df = df.drop(columns=["__ceo_events__"])

    return df


def clean_number(x):
    if pd.isna(x):
        return np.nan

    if isinstance(x, str):
        x = x.replace(" ", "")   # tar bort tusentals-mellanslag
        x = x.replace(",", "")   # ifall det finns decimalformat
        x = x.replace("-", "")

    try:
        return float(x)
    except:
        return np.nan



def CEO_change(df):

    def extract_years(value):
        if pd.isna(value):
            return []

        parts = str(value).split("|")
        years = []

        for p in parts:
            p = p.strip()

            if p in ["", "-", "*"]:
                continue

            try:
                years.append(int(str(p)[:4]))
            except:
                continue

        return years

    df["__ceo_events__"] = (
        df["External CEO - Date appointed"].apply(extract_years) +
        df["CEO - Date appointed"].apply(extract_years)
    )

    def compute_change(row):
        year = row["year"]
        events = row["__ceo_events__"]

        # 1 om exakt detta år finns i events
        return int(year in events)

    df["CEO_change"] = df.apply(compute_change, axis=1)

    df = df.drop(columns=["__ceo_events__"])

    return df


def CEO_change_any(df):

    df["CEO_change_any"] = 0

    for company in df["Company name"].unique():

        temp = df[df["Company name"] == company]

        has_change = (
            temp.loc[temp["year"].isin([2021, 2022, 2023, 2024]), "CEO_change"]
            .eq(1)
            .any()
        )

        if has_change:

            df.loc[df["Company name"] == company, "CEO_change_any"] = 1

    return df



def book_to_market_ratio(df):
    #transform market cap from millions to tkr
    df['market_cap'] = df['market_cap'] * 1000
    df["book_to_market_ratio"] = np.log(df['total_equity']/df['market_cap'])
    return df


def DELTA_book_to_market_ratio(df):
    df["delta_book_to_market_ratio"] = (
        df.groupby("Company name")["book_to_market_ratio"]
        .diff()
    )
    return df







#requirer file path, marcet cap file

def add_market_cap(panel_df):

    df_data = pd.read_excel(
        "file path",
        sheet_name="Current Screen Template",
        header=None
    )

    fy_to_year = {
        "FY-1": 2024,
        "FY-2": 2023,
        "FY-3": 2022,
        "FY-4": 2021,
        "FY-5": 2020,
    }

    panel_df["market_cap"] = np.nan

    for idx, row_panel in panel_df.iterrows():

        parts_1 = str(row_panel["Company name"]).lower().split()

        if len(parts_1) == 0:
            continue

        if parts_1[0] in ["aktiebolaget", "fastighets", "beijer"]:
            name_1 = " ".join(parts_1[:2])
        else:
            name_1 = parts_1[0]

        year = row_panel["year"]

        fy_col = None
        for fy, fy_year in fy_to_year.items():
            if fy_year == year:
                fy_col = fy
                break

        if fy_col is None:
            continue


        # B = 1 (company name)
        # F = 5 (FY-1)
        fy_map = {
            "FY-1": 5,
            "FY-2": 6,
            "FY-3": 7,
            "FY-4": 8,
            "FY-5": 9
        }

        col_idx = fy_map[fy_col]

        for _, row_data in df_data.iterrows():

            name_2 = str(row_data.iloc[1]).lower().split()

            if len(name_2) == 0:
                continue

            if name_2[0] in ["aktiebolaget", "fastighets", "beijer"]:
                name_2 = " ".join(name_2[:2])
            else:
                name_2 = name_2[0]

            if name_1 == name_2:

                value = row_data.iloc[col_idx]

                if isinstance(value, str):
                    value = value.replace("\xa0", "")
                    value = value.replace(" ", "")
                    value = value.replace(",", ".")

                panel_df.at[idx, "market_cap"] = pd.to_numeric(value, errors="coerce")

                break

    return panel_df














file_path = #raw data from 

sheet_name = "Selected fields" #....

output_file = #output file




def main():

    # Meta data columns (copy each year)
    static_columns = [
        "Company name",
        "Branch",
        # "Currency",
        # "Last submitted",
        "Formed date",
        "CEO - Name",
        "External CEO - Date appointed",
        "Acting CEO - Date appointed",
        "CEO - Date appointed"
    ]

    # year dependent variables
    yearly_variables = {
        "Consolidated financial statement": "consolidated_financial_statement",
        "Operating profit/loss (EBIT) (tkr)": "ebit",
        "Total assets (tkr)": "total_assets",
        "Net sales (tkr)": "net_sales",
        "Total current liabilities (tkr)": "current_liabilities",
        "Total long-term liabilities (tkr)": "long_term_liabilities",
        "Total equity (tkr)": "total_equity",
        "Minority interests and profit/loss in subsidiaries (tkr)": "minority_interest",
        "Untaxed reserves (tkr)": "untaxed_reserves",
        "Provisions (tkr)": "provisions"
    }

    df = pd.read_excel(file_path, sheet_name)

    financial_cols = [
        col for col in df.columns
        if any(key in col for key in yearly_variables.keys())
    ]

    df[financial_cols] = df[financial_cols].applymap(clean_number)

    # years
    years = [2024, 2023, 2022, 2021, 2020]

    panel_df = build_panel(df, years)

    panel_df = panel_df.sort_values(
        by=["Company name", "year"]
    ).reset_index(drop=True)

    panel_df = DELTA_total_assets(panel_df)

    panel_df = sale_growth(panel_df)
    panel_df = DELTA_sale_growth(panel_df)

    panel_df = leverage(panel_df)
    panel_df = DELTA_leverage(panel_df)

    panel_df = roa(panel_df)
    panel_df = DELTA_roa(panel_df)

    panel_df = firm_age(panel_df)

    panel_df = CEO_tenure(panel_df)

    panel_df = CEO_change(panel_df)

    panel_df = CEO_change_any(panel_df)

    cols = panel_df.columns.tolist()
    print(panel_df)
    cols.remove("year")

    panel_df = panel_df[["Company name", "year"] + cols[1:]]

    panel_df = add_market_cap(panel_df)

    panel_df = book_to_market_ratio(panel_df)

    panel_df = DELTA_book_to_market_ratio(panel_df)

    panel_df.to_csv(output_file, index=False)


if __name__ == "__main__":
    main()
