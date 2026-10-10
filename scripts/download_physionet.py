from pathlib import Path
import os
import wfdb

ROOT = Path(__file__).resolve().parents[1]
DB_NAME = 'ctu-uhb-ctgdb'
LOCAL_DIR = str(ROOT / 'data' / 'ctu-uhb-ctgdb')
SUBSET_SIZE = 15  # download first N records for initial EDA

print("=" * 60)
print("DATASET C: PhysioNet CTU-UHB CTG Database")
print("=" * 60)

# Try to get the record list first
try:
    record_list = wfdb.get_record_list(DB_NAME)
    print(f"Total records available: {len(record_list)}")
    print(f"First 10 record names: {record_list[:10]}")
except Exception as e:
    print(f"Could not get record list: {e}")
    record_list = []

# Download subset
records_to_dl = record_list[:SUBSET_SIZE] if record_list else []
print(f"\nAttempting to download {len(records_to_dl)} records (subset)...")

os.makedirs(LOCAL_DIR, exist_ok=True)

downloaded = []
failed = []
for rec_name in records_to_dl:
    try:
        wfdb.dl_database(DB_NAME, LOCAL_DIR, records=[rec_name])
        downloaded.append(rec_name)
        print(f"  Downloaded: {rec_name}")
    except Exception as e:
        failed.append((rec_name, str(e)))
        print(f"  FAILED: {rec_name} -> {e}")

print(f"\nDownloaded: {len(downloaded)}/{len(records_to_dl)} records")
if failed:
    print(f"Failed: {len(failed)} records")

# Verify downloaded records
print("\n--- Verifying downloaded records ---")
local_files = os.listdir(LOCAL_DIR)
hea_files = [f for f in local_files if f.endswith('.hea')]
dat_files = [f for f in local_files if f.endswith('.dat')]
print(f"Local .hea files: {len(hea_files)}")
print(f"Local .dat files: {len(dat_files)}")

# Read sample record metadata
if downloaded:
    sample_rec = downloaded[0]
    print(f"\n--- Sample Record Metadata: {sample_rec} ---")
    try:
        record = wfdb.rdrecord(os.path.join(LOCAL_DIR, sample_rec))
        print(f"  Record name: {record.record_name}")
        print(f"  Number of signals: {record.n_sig}")
        print(f"  Sampling frequency: {record.fs} Hz")
        print(f"  Signal length: {record.sig_len} samples")
        print(f"  Duration: {record.sig_len / record.fs:.1f} seconds ({record.sig_len / record.fs / 60:.1f} minutes)")
        for i, name in enumerate(record.sig_name):
            print(f"  Signal {i}: {name} ({record.units[i]})")
    except Exception as e:
        print(f"  Error reading record: {e}")

print("\nPhysioNet download complete!")
