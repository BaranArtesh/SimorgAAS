# import pandas as pd
# from dateutil.parser import parse

# def filter_data_with_pandas(data: dict) -> dict:
#     """
#     Cleans WHOIS and IPInfo data dictionaries using pandas for filtering out empty or messy values.
#     Field-aware enhancements are added for better data normalization.
#     """
#     if not data or not isinstance(data, dict):
#         return {}

#     df = pd.Series(data)

#     # Step 1: Drop fields that are None, NaN, or empty strings
#     df = df.dropna().replace('', pd.NA).dropna()

#     def clean_value(val):
#         if isinstance(val, str):
#             val = val.strip()
#             return val if val else None
#         elif isinstance(val, list):
#             cleaned = list({str(v).strip() for v in val if v and str(v).strip()})
#             return cleaned if cleaned else None
#         elif isinstance(val, dict):
#             return val  # You can decide to flatten this if needed
#         return val

#     df = df.apply(clean_value)
#     df = df.dropna()

#     # --- Specific field handling ---
#     # Normalize emails to lowercase
#     if 'emails' in df and isinstance(df['emails'], list):
#         df['emails'] = [email.lower() for email in df['emails'] if '@' in email]

#     email_fields = [
#         "abuse_contact_email", "admin_contact_email", "noc_contact_email"
#     ]
#     for field in email_fields:
#         if field in df and isinstance(df[field], str):
#             df[field] = df[field].lower()

#     # Normalize country/state fields to uppercase
#     for field in ['country', 'org_country', 'asn_country_code', 'state', 'org_state']:
#         if field in df and isinstance(df[field], str):
#             df[field] = df[field].upper()

#     # Parse and format date fields
#     def parse_date_safe(val):
#         try:
#             return parse(val).strftime('%Y-%m-%d %H:%M:%S') if val else None
#         except Exception:
#             return None

#     date_fields = ['updated_date', 'creation_date', 'expiration_date', 'asn_date']
#     for field in date_fields:
#         if field in df:
#             if isinstance(df[field], list):
#                 # Choose the most recent valid one from the list
#                 parsed_dates = [parse_date_safe(d) for d in df[field] if d]
#                 df[field] = max(parsed_dates) if parsed_dates else None
#             else:
#                 df[field] = parse_date_safe(df[field])

#     # Standardize name_servers as a sorted list
#     if 'name_servers' in df and isinstance(df['name_servers'], list):
#         df['name_servers'] = sorted({ns.lower() for ns in df['name_servers']})

#     # Clean text-heavy fields
#     for field in ['status', 'asn_description', 'org_name', 'address', 'org_street']:
#         if field in df and isinstance(df[field], str):
#             df[field] = ' '.join(df[field].split())

#     return df.to_dict()


import pandas as pd

def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def filter_data_with_pandas(raw_data_list):
    flat_data = []

    for raw_data in raw_data_list:
        try:
            flattened = flatten_dict(raw_data)
            flat_data.append(flattened)
        except Exception as e:
            print(f"[!] Error flattening data: {e}")
            continue

    df = pd.DataFrame(flat_data)

    # Replace NaNs with None (so they map to NULL in DB if needed)
    df = df.where(pd.notnull(df), None)

    # Filter only needed columns for storage
    columns_to_keep = [
        'ip', 'asn', 'asn_registry', 'asn_cidr', 'asn_date', 'asn_country_code', 'asn_description',
        'network_name', 'network_handle', 'network_status', 'network_start_address',
        'network_end_address', 'network_cidr', 'network_type', 'network_parent_handle',
        'org_street', 'abuse_contact_name', 'abuse_contact_email', 'abuse_contact_phone'
    ]

    # Only keep those columns if they exist
    filtered_df = df[[col for col in columns_to_keep if col in df.columns]]
    return filtered_df.to_dict(orient='records')

