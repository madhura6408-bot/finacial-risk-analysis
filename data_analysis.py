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

for col in df.columns:
    df[col] = df[col].astype(str).str.strip().str.strip('"')

df = df.replace(["", "nan", "None"], pd.NA)

print("DATA ANALYSIS")
print("Total Records:", len(df))
print("Total Missing Values:", df.isnull().sum().sum())

print("\nMissing Values in Each Column:")
print(df.isnull().sum())

print("\nDuplicate Records:", df.duplicated().sum())

print("\nEXPLORATORY DATA ANALYSIS")

df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

print("\nTransaction Amount Analysis")
print("Minimum Amount:", df["amount"].min())
print("Maximum Amount:", df["amount"].max())
print("Average Amount:", df["amount"].mean())
print("Total Amount:", df["amount"].sum())

print("\nTransaction Types")
print(df["Transaction_Type"].value_counts())

print("\nTransaction Channels")
print(df["channel"].value_counts())

print("\nTransaction Regions")
print(df["region"].value_counts())

# FINAL CLEANED DATASET REPORT

cleaned_df = pd.read_csv("cleaned_transaction.csv")

print("\nFINAL DATASET REPORT")
print("Total Records:", len(cleaned_df))
print("Missing Values:", cleaned_df.isnull().sum().sum())
print("Duplicate Records:", cleaned_df.duplicated().sum())

print("\nAmount Statistics")
stats = df["amount"].describe()

stats = stats.rename({
    "count": "Total Transactions",
    "Average": "Average Amount",
    "min": "Minimum Amount",
    "25%": "25% Transactions",
    "50%": "Median Amount",
    "75%": "75% Transactions",
    "max": "Maximum Amount"
})
for name, value in stats.items():
    print(f"{name}: {value:.2f}")

print("\nFINAL SUMMARY")

print("Total Transactions:", len(df))

print("Average Transaction Amount:",
      f"{df['amount'].mean():.2f}")

print("Minimum Transaction Amount:",
      f"{df['amount'].min():.2f}")

print("Maximum Transaction Amount:",
      f"{df['amount'].max():.2f}")

print("Total Transaction Amount:",
      f"{df['amount'].sum():.2f}")

