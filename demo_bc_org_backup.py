### Exporting a backup for a Business Class organization via the Trello API ###########
#
# If you're just getting started, check out demo.py. I'm going to make a lot of assumptions
# in this tutorial assuming you've already gone through demo.py
#
# This demo file will show you how to use an undocumented feature of the Trello API
# to automate backing up your organization's data
#


import requests
import json
from pprint import pprint
import sys
import time

import argparse # using argparse for id_organization and attachments

########### command line arguments here vvv   ###############################
#
#
parser = argparse.ArgumentParser(description='Get a backup of your organization data in Trello. Requires Business Class.')
parser.add_argument('--id_organization', dest='id_organization', required=True,
                   default=None,
                   help='the id of the organization. The orgname will also work, but NB the orgname can change and id cannot.')
parser.add_argument('--download_attachments', dest='download_attachments',
                   action='store_true', default=False,
                   help='decide if you want to download attachments. Default is false.')
parser.add_argument('--attachment_age', dest='attachment_age',
                   type=int, default=0,
                   help='should be a number between 0 and 3650 (default: 0); which attachments should be in the export. If 0, gets all of them; if anything else, gets only attachments uploaded the past `attachment_age` days.')
parser.add_argument('--poll_interval', dest='poll_interval',
                   type=int, default=60,
                   help='Time interval, in seconds, for often this script will check to see if the download is available. Please do not use less than 60 in production.')
parser.add_argument('--out_file', dest='out_file',
                   default='export.zip',
                   help='the id of the organization. The orgname will also work, but NB the orgname can change and id cannot.')
command_line_args = parser.parse_args()
id_organization = command_line_args.id_organization
download_attachments = command_line_args.download_attachments
attachment_age = command_line_args.attachment_age
poll_interval = command_line_args.poll_interval
out_file = command_line_args.out_file
#
#
##############################################################################


# Set key and token here or get it from settings.py (preferred)
key = ''
# if you're storing your key in this file, you don't need the following three lines
if not key:
  from settings import trello_key 
  key = trello_key

token = ''
# if you're storing your token in this file, you don't need the following three lines
if not token:
  from settings import trello_token 
  token = trello_token

params_key_and_token = {'key':key,'token':token}

# base API URL
base = 'https://trello.com/1/'

### Request a backup and get a token ###################################
#
#
url = '%sorganizations/%s/export' % (base, id_organization)
args = {'attachments': str(download_attachments).lower(), 'attachment_age': attachment_age}
response = requests.get(url, params=params_key_and_token, data=args)

if response.status_code != 200:
  print 'We did not get a token back. Maybe a problem with your id_organization or maybe you have not upgraded to Business Class?'
  response.raise_for_status()
  sys.exit()

export_token = response.json()['token']

#Now that we have an export token, we'll periodically check to see if it's available

complete = False
download_url = ''

while not complete:
  url = '%sorganizations/%s/export/%s/status' % (base, id_organization, export_token)
  response = requests.get(url, params=params_key_and_token)
  response_dict = response.json()
  #we should eventually get back a URL in 'complete'
  if response_dict['complete']:
    download_url = 'https://trello.com%s' % response_dict['complete']
    break

  has_progress = 'progress' in response_dict['status'] and 'total' in response_dict['status']

  if has_progress:
    print '%s: %s of %s' % (response_dict['status']['stage'], response_dict['status']['progress'], response_dict['status']['total'])
  else:
    print response_dict['status']['stage']

  time.sleep(poll_interval)

print download_url



#now we're going to make a request for the actual downloaded file and write it to out_file
response = requests.get(download_url, stream=True)
if not response.ok:
  print 'something went wrong'
  response.raise_for_status()

with open(out_file, 'wb') as f:
  for chunk in response.iter_content(chunk_size=1024):
    if chunk:
      f.write(chunk)
      f.flush()

print 'organization export downloaded to %s' % out_file