### Managing an organization using the Trello API ###########
#
# If you're just getting started, check out demo.py. I'm going to make a lot of assumptions
# in this tutorial assuming you've already gone through demo.py
#
# This demo file will highlight several of the things that you can do to manage 
# a Trello organization, such as viewing organizations, boards, and members.
#


import requests
import json
from pprint import pprint
import sys

# If you're just getting started, check out demo.py. I'm going to make a lot of assumptions
# in this tutorial assuming you've already gone through demo.py

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

### Managing organization basics: Am I an admin? ######################
#
# First, let's get our member ID, so we can compare it later on
url = base + 'members/me'
args = {'fields': 'id'}
response = requests.get(url, params=params_key_and_token, data=args)
id_member_me = response.json()['id']


# Let's start by getting a list of organizations that I belong to
# docs: https://trello.com/docs/api/member/index.html#get-1-members-idmember-or-username-organizations

url = base + 'members/me/organizations'

# Let's ask for the following info:
# - name
# - idBoards - so we can check out the boards in the orgs
# - membersships - so we know which members belong to the org
# - premiumFeatures - so we know what we can do with the org (if we've paid)
args = {'fields': 'name,idBoards,memberships,premiumFeatures'}
response = requests.get(url, params=params_key_and_token, data=args)

response_my_orgs = response.json()

# Let's make a helper method to find a member based on id within an org
def find_member(org, id_member):
  for member in org['memberships']:
    if member['idMember'] == id_member:
      return member
  return False

#let's make a method to determine if I'm an admin for an org
def am_i_admin(org):
  member = find_member(org, id_member_me)
  return (member and member['memberType'] == 'admin')

#print the names of the orgs for which I'm an admin
for org in response_my_orgs:
  if am_i_admin(org):
    print org['name']

#
###################################

### Deactivate or remove someone who left the company ###########
#
# Let's say you have the email address of someone who left your organization
# and you want to remove them from the organizations that you manage.
#
# NB: People who sign up for Trello can use any email address they choose, meaning
#     they may or may not have used an official company email.

email_of_user_who_left = 'joe@example.com'

# using https://trello.com/docs/api/search/index.html#get-1-search-members
url = base + 'search/members'

response = requests.get(url, params=params_key_and_token, data={'query': email_of_user_who_left, 'limit': 1})
response_members = response.json()

if 'id' in response_members[0]:
  id_member_who_left = response_members[0]['id']
else:
  id_member_who_left = None

# Let's make a method for determining if I can deactivate a user
def can_deactivate(org):
  return 'deactivated' in org['premiumFeatures']

# And let's make a method to either deactivate or remove a member
# NB: if your organization has Business Class, you can deactivate a member, which will
#     remove access too all of the boards for that member, while still letting you see
#     what they belonged to. Removing a member doesn't remove them from the boards to
#     which they belonged.
# We're going to throw in an execute parameter so we can do a dry run first

def deactivate_or_remove(org, id_member, execute=False):
  #gotta be an admin
  if not am_i_admin(org):
    print 'not an admin of org %s' % org['name']
    return

  if not find_member(org, id_member):
    print 'member %s does not belong to org %s' % (id_member, org['name'])

  to_print = ''

  if can_deactivate(org):
    if execute:
      url = '%sorganizations/%s/members/%s/deactivated' % (base, org['id'], id_member)
      # NB: for 'value' we need to provide a string, not a Python boolean
      response = requests.put(url, params=params_key_and_token, data={'id': id_member, 'value': 'true'})
    else:
      to_print = 'dry run: '

    print '%sdeactivated member %s from org %s' % (to_print, id_member, org['name'])
  else:
    if execute:
      url = '%sorganizations/%s/members/%s' % (base, org['id'], id_member)
      response = requests.delete(url, params=params_key_and_token, data={'id': id_member})
    else:
      to_print = 'dry run: '

    print '%sremoved member %s from org %s' % (to_print, id_member, org['name'])

# Now let's make sure we have an id_member_who_left (from above) and remove the member
if id_member_who_left:
  for org in response_my_orgs:
    deactivate_or_remove(org, id_member_who_left, execute=False)

#
#
#########################################################

### Organization lock down ##############################
#
# Let's say I want to lock down my organization so that only people who are a 
# member of the organization can be a member of boards. We'll start by making
# a few helper methods

# This method will disable external members from joining boards
def can_disable_external_members(org):
  return 'disableExternalMembers' in org['premiumFeatures']

# If you have Business Class, you can disable external members for your organization, which 
# you would want to do if you're locking everything down
def disable_external_members(org, execute=False):
  if not am_i_admin(org):
    print 'not an admin of org %s' % org['name']
    return

  if not can_disable_external_members(org):
    print 'cannot disable external members for org %s' % org['name']

  to_print = ''
  
  if execute:
    url = '%sorganizations/%s/prefs/externalMembersDisabled' % (base, org['id'])
    response = requests.put(url, params=params_key_and_token, data={'value': 'true'}) #not tested
  else:
    to_print = 'dry run:'

  print '%sdisabled external members for org %s' % (to_print, org['name'])

# Business Class org admins can admin all the boards in the org, even if they're
# not explicitly members of that org.
def am_i_super_admin(org):
  org_has_super_admins = 'superAdmins' in org['premiumFeatures']
  return org_has_super_admins and am_i_admin(org)

# We need a helper method to determine if we're an admin of the board.
# This is only necessary if the org does not have Business Class
def is_board_admin(id_board, id_member):
  url = '%sboards/%s/members' % (base, id_board)
  args = {'filter': 'admins', 'fields': 'username'}
  response = requests.get(url, params=params_key_and_token, data=args)
  response_arr = response.json()
  for member in response_arr:
    if member['id'] == id_member:
      return True
  return False

# this method will remove a member from the board if we have permissions
def remove_member_from_board(id_board, id_member, org, execute = False):
  #we have to be an admin of either a Business Class org or the individual board
  if not (am_i_super_admin(org) or is_board_admin(id_board, id_member_me)):
    print 'not an admin of board %s' % id_board
    return

  to_print = ''
  
  if execute:
    url = '%sboards/%s/members/%s' % (base, id_board, id_member)
    response = requests.delete(url, params=params_key_and_token, data={'idMember': id_member}) #not tested
  else:
    to_print = 'dry run:'

  print '%sremoved member %s from board %s' % (to_print, id_member, id_board)

# Now that we've defined our helper methods, lets iterate through the boards in each org and remove 
# members who don't belong to the organization

for org in response_my_orgs:
  #make sure I'm an admin first
  if not am_i_admin(org):
    print 'I am not an admin of org %s' % org['name']
    continue

  # then let's disable external members

  disable_external_members(org, execute = False)

  # now let's iterate through the list of boards, looking at the members to see if they belong to the org
  for id_board in org['idBoards']:
    # Get the board membership
    url = '%sboards/%s/members' % (base, id_board)
    args = {'fields': 'username'}
    response = requests.get(url, params=params_key_and_token, data=args)
    response_members = response.json()

    # loop through the members
    for member in response_members:
      # check if the member belongs to the org
      if not find_member(org, member['id']):
        # if not, remove them the board
        remove_member_from_board(id_board, member['id'], org, execute = False)

# If you mainly wanted to use this for informational purposes, and not actually to remove people, you could 
# query the Trello API for more information about the boards and members so the output gave you more information.
#
#####################################################################





