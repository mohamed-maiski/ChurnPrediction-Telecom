import argparse
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'data/raw/telco_customers.csv')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('The destination already exists. Choose another output path to preserve your data.')
    with urlopen(SOURCE, timeout=30) as response:
        data = response.read(10 * 1024 * 1024 + 1)
    if len(data) > 10 * 1024 * 1024 or not data.startswith(b'customerID,'):
        raise ValueError('The downloaded file does not match the expected dataset format.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(args.output)


if __name__ == '__main__':
    main()
