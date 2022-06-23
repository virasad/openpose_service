import requests
import argparse

request_parser = argparse.ArgumentParser(description='Request to the API')
request_parser.add_argument(
    '-u', '--url', help='URL to request', default='http://localhost:8000/inference')
request_parser.add_argument(
    '-f', '--file', help='File to infer', required=True)
args = request_parser.parse_args()
files = {'image': open(args.file, 'rb')}
response = requests.post(args.url, files=files)
print(response.text)
