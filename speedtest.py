import os
import re
import subprocess
import time
import boto3
import time
import argparse
from datetime import datetime
from botocore.config import Config

parser = argparse.ArgumentParser(description='Argument parse.')
parser.add_argument('--single', action='store_true')
parser.add_argument('-p', '-path', help='speedtest-cli path.')
args = parser.parse_args()

# Get environment variables
access_key = os.getenv('AWS_ACCESS_KEY')
secret_key = os.environ.get('AWS_SECRET_KEY')
cli_path = args.p if hasattr(args, 'p') else '/usr/local/bin/'

if args.single:
    print("Running single instance")
else:
    print("Running daemon")

my_config = Config(
    region_name='us-west-2',
    signature_version='v4',
    retries={
        'max_attempts': 10,
        'mode': 'standard'
    }
)

client = boto3.client('cloudwatch', aws_access_key_id=access_key, aws_secret_access_key=secret_key,
                      config=my_config)


def publish_value(metric_name, value):
    response = client.put_metric_data(
        Namespace='Raspi1',
        MetricData=[
            {
                'MetricName': metric_name,
                'Dimensions': [
                    {
                        'Name': 'Network',
                        'Value': 'SpeedTest'
                    },
                ],
                'Timestamp': datetime.now().timestamp(),
                'Value': value,
                'Unit': 'None',
                'StorageResolution': 1
            },
        ]
    )
    response_meta = response["ResponseMetadata"]
    if response_meta["HTTPStatusCode"] == 200:
        pass
    else:
        print("Unable to submit metric: {}".format(response))


while True:
    response = subprocess.Popen(cli_path + 'speedtest-cli --simple', shell=True, stdout=subprocess.PIPE).stdout.read().decode('utf-8')

    ping = re.findall('Ping:\s(.*?)\s', response, re.MULTILINE)
    download = re.findall('Download:\s(.*?)\s', response, re.MULTILINE)
    upload = re.findall('Upload:\s(.*?)\s', response, re.MULTILINE)

    ping = ping[0].replace(',', '.')
    download = download[0].replace(',', '.')
    upload = upload[0].replace(',', '.')

    print("Publishing ping:{}, upload:{}, dowload:{}".format(ping, upload, download))

    publish_value("ping", float(ping))
    publish_value("download", float(download))
    publish_value("uplaod", float(upload))

    if args.single:
        break

    time.sleep(30)


