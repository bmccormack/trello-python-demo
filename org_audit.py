# I'm going to use query_trello from trello_helper.py and am going to
# minimally comment this file compared to the demo files.

from trello_helper import query_trello
from util import jprint
import sys

id_org = '4e387d48d875071b270040e8'

def get_org_memberships(id_org):
  url = 'organization/%s/memberships?member=true' % id_org
  resp = query_trello('GET', url)
  return resp.json()

def get_org_members_normal_and_admin(org_membership):
  return [m for m in org_membership if m["memberType"] in ['normal', 'admin'] and not m['deactivated']]

def get_org_members_deactivated(org_membership):
  return [m for m in org_membership if m['deactivated']]

def get_org_boards(id_org):
  url = 'organization/%s/boards?filter=all&fields=closed,name,shortUrl' % id_org
  resp = query_trello('GET', url)
  return resp.json()

def get_member_list_from_org_membership(org_memberships):
  members = []
  for membership in org_memberships:
    member = membership["member"]
    member["org_member"] = True
    member["org_deactivated"] = membership["deactivated"]
    member["unconfirmed"] = membership["unconfirmed"]
    member["org_member_type"] = membership["memberType"]
    member["boards_with_membership_info"] = []
    members.append(member)
  return members

def get_board_memberships(id_board):
  url = 'board/%s/memberships?member=true' % id_board
  resp = query_trello('GET', url)
  return resp.json()

def add_board_member_to_member_list(board_membership, board, member_list):
  board_with_membership_info = board
  board_with_membership_info["board_deactivated"] = board_membership["deactivated"]
  board_with_membership_info["board_member_type"] = board_membership["memberType"]

  members = [m for m in member_list if m["id"] == board_membership["idMember"]]
  if members:
    member = members[0]
    member["boards_with_membership_info"].append(board_with_membership_info)
  else:
    member = board_membership["member"]
    member["org_member"] = False
    member["org_deactivated"] = False
    member["unconfirmed"] = board_membership["unconfirmed"]
    member["org_member_type"] = None
    member["boards_with_membership_info"] = [board_with_membership_info]
    member_list.append(member)    


org_memberships = get_org_memberships(id_org)
org_memberships_normal_and_admin = get_org_members_normal_and_admin(org_memberships)
get_org_memberships_deactivated = get_org_members_deactivated(org_memberships)
org_boards = get_org_boards(id_org)
member_list = get_member_list_from_org_membership(org_memberships)


for board in org_boards:
  board_memberships = get_board_memberships(board["id"])
  for board_membership in board_memberships:
    add_board_member_to_member_list(board_membership, board, member_list)

  # get the members of this board who are not members of the organization
  # add the non-org members to a dictionary of external members
  # get the members of this board who are deactivated members of the organization
  # add the deactivated members to a dictionary of external members


jprint(member_list)
sys.exit()


# Confirmed Members
# Unconfirmed Members
# Deactivated Members
# Non-org members
# Somewhere down here we want to print out who has access to what, in a top-level way, e.g.:
# Name, username, unconfirmed, deactivated, number of boards visible, number of boards deactivated
#
# and then after that, a full break down by user
# Name, username, unconfirmed, deactivated
# Board Name, board URL, member type