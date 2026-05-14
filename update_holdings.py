import pandas as pd

# Read the current holdings file
df = pd.read_csv('wiki/holdings_structured.csv')

# Official names mapping
name_mapping = {
    'AESG': 'iShares Global Aggregate Bond ESG (AUD Hedged) ETF',
    'EMXC': 'iShares MSCI Emerging Markets ex China ETF',
    'GLDN': 'iShares Physical Gold ETF',
    'GLIN': 'iShares Core FTSE Global Infrastructure (AUD Hedged) ETF',
    'GLPR': 'iShares Core FTSE Global Property Ex Au (AUD Hedged) ETF',
    'IACT': 'iShares U.S. Factor Rotation Active ETF',
    'IAF': 'iShares Core Composite Bond ETF',
    'ICOR': 'iShares Core Corporate Bond ETF',
    'IEM': 'iShares MSCI Emerging Markets ETF',
    'IEU': 'iShares Europe AUD ETF',
    'IGB': 'iShares Treasury ETF',
    'IHHY': 'iShares Global High Yield Bond (AUD Hedged) ETF',
    'IHVV': 'iShares S&P 500 AUD Hedged ETF',
    'IJP': 'iShares MSCI Japan ETF',
    'ILB': 'iShares Government Inflation Bond ETF',
    'IOZ': 'iShares Core S&P/ASX 200 ETF',
    'ISEC': 'iShares Cash ETF',
    'IVV': 'iShares S&P 500 ETF',
    'IZZ': 'iShares China Large-Cap ETF',
    'CASHACCT': 'Cash Account'
}

# Update holding names based on Unit_ID
df['Holding_name'] = df['Unit_ID'].map(name_mapping)

# Save the corrected file
df.to_csv('wiki/holdings_structured_corrected.csv', index=False)
print("Updated holdings file created: wiki/holdings_structured_corrected.csv")
print(f"Total holdings: {len(df)}")
print(f"Portfolio models: {df['Portfolio_short'].nunique()}")
