import pandas as pd

df = pd.read_csv("transaction.csv", sep="|", quotechar='"', engine="python")

if len(df.columns) == 1:
    df = df.iloc[:, 0].str.split(r"\t", expand=True)
    df.columns = [
        "Transaction_ID",
        "Account_ID",
        "Transaction_datetime",
        "amount",
        "Transaction_Type",
        "channel",
        "region"
    ]

# Remove extra quotation marks and spaces
for col in df.columns:
    df[col] = df[col].astype("string").str.strip().str.strip('"')

df = df.replace(["", "nan", "None"], pd.NA)

df["amount"] = pd.to_numeric(
    df["amount"], errors="coerce"
).astype("float64")

df["amount"] = df["amount"].fillna(df["amount"].median())

mode_value = df["Transaction_Type"].mode()

if not mode_value.empty:
    df["Transaction_Type"] = df["Transaction_Type"].fillna(mode_value[0])

df = df.drop_duplicates()

df.to_csv("cleaned_transaction.csv", index=False)

print("DATA CLEANING RESULTS")
print("Total Records:", len(df))
print("Missing Values:", df.isnull().sum().sum())
print("Duplicate Records:", df.duplicated().sum())
print("Cleaned dataset saved successfully.")

