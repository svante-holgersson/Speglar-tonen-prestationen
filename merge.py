import pandas as pd

df1 = pd.read_csv("") #select tone file
df2 = pd.read_csv("") #select finance file



df1["company_clean"] = df1["company"].replace(name_map)
df2["company_clean"] = df2["Company name"].replace(name_map)


df1["year"] = pd.to_numeric(df1["year"], errors="coerce").astype("Int64")
df2["year"] = pd.to_numeric(df2["year"], errors="coerce").astype("Int64")

#dropp 2020
df1 = df1[df1["year"] != 2020]
df2 = df2[df2["year"] != 2020]



df1 = df1.drop_duplicates(subset=["company_clean", "year"])
df2 = df2.drop_duplicates(subset=["company_clean", "year"])


check = df2.merge(df1, on=["company_clean", "year"], how="left", indicator=True)

unmatched = check[check["_merge"] == "left_only"]

print("\nMATCH DISTRIBUTION:")
print(check["_merge"].value_counts())

df_combined = df2.merge(
    df1,
    on=["company_clean", "year"],
    how="left",
    validate="one_to_one"
)



# SORT
df_combined = df_combined.sort_values(["company_clean", "year"])


# SAVE
df_combined.to_csv(
    "master_file_path/name",
    index=False
)


unmatched.to_csv(
    "debug_file_path/name",
    index=False
)
