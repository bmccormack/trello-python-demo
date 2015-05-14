# I'm going to use query_trello from trello_helper.py and am going to
# minimally comment this file compared to the demo files.

from trello_helper import query_trello
from util import jprint
from texttable import Texttable
from copy import deepcopy
import argparse
import sys

# README
#
# This report is intended to show you who is a member of your organization and the boards
# within the organization. If you run it with just the --org arg, you're going to get a summary
# of all users, listed by org members at the top and non-org members at the bottom, followed by
# a full report of all the boards each member can access. Use the other args to limit what gets
# printed out.
#
# A few things:
# - Deactivated and unconfirmed users cannot see resources that they are a member of.
# - Unconfirmed members *can* see a resource if they were the one who created that resource, in which case
#   the user will show up as Unconfirmed = False for that particular board or organization. This is rare.
# - "Readable" means "Can the member see the board based on their unconfirmed and deactivated status?".
#   Readable does *not* take into account whether a board is public or org-visible boards. (A TODO would
#   be to add an option to print out reports by board and not by member, but you kind of already get that
#   by looking up the board in Trello and looking at the members area.)
# - Pay attention to "org member type" in the summary report. It shows admins first, followed by normal members,
#   followed by people who are not members of the organization (None).
# - If you have a ton of boards in your organization, you might get rate-limited. (Sorry). Email me and I can 
#   try to fix that.

parser = argparse.ArgumentParser(description="Find Trello members who have access to organization resources.")
parser.add_argument("--org", help="the id of the organization or the orgname", required=True)
parser.add_argument("--summary", help="print only the summary of users", action="store_true")
parser.add_argument("--all", help="print the summary and board details for all users", action="store_true")
parser.add_argument("--user", help="print only the board details for a particular user")

args = parser.parse_args()
id_org = args.org

def get_org_memberships(id_org):
  url = 'organization/%s/memberships?member=true' % id_org
  resp = query_trello('GET', url)
  return resp.json()

def get_org_members_normal_and_admin(org_membership):
  return [m for m in org_membership if m["memberType"] in ['normal', 'admin'] and not m['deactivated']]

def get_org_members_deactivated(org_membership):
  return [m for m in org_membership if m['deactivated']]

def get_org_boards(id_org):
  url = 'organization/%s/boards?filter=all&fields=closed,name,shortUrl,shortLink' % id_org
  resp = query_trello('GET', url)
  return resp.json()

def get_member_list_from_org_membership(org_memberships):
  members = []
  for membership in org_memberships:
    member = deepcopy(membership["member"])
    member["org_member"] = True
    member["org_deactivated"] = membership["deactivated"]
    member["org_unconfirmed"] = membership["unconfirmed"]
    member["org_member_type"] = membership["memberType"]
    member["boards_with_membership_info"] = []
    members.append(member)
  return members

def get_board_memberships(id_board):
  url = 'board/%s/memberships?member=true' % id_board
  resp = query_trello('GET', url)
  return resp.json()

def add_board_member_to_member_list(board_membership, board, member_list):
  board_with_membership_info = deepcopy(board)

  board_with_membership_info["board_unconfirmed"] = board_membership["unconfirmed"]
  board_with_membership_info["board_deactivated"] = board_membership["deactivated"]
  board_with_membership_info["board_member_type"] = board_membership["memberType"]
  board_with_membership_info["board_readable_to_user"] = not board_membership["unconfirmed"] and not board_membership["deactivated"]

  members = [m for m in member_list if m["id"] == board_membership["idMember"]]
  if members:
    member = members[0]
    member["boards_with_membership_info"].append(board_with_membership_info)
    #if
  else:
    member = board_membership["member"]
    member["org_member"] = False
    member["org_deactivated"] = False
    member["org_unconfirmed"] = None
    member["org_member_type"] = None
    member["boards_with_membership_info"] = [board_with_membership_info]
    member_list.append(member)    


def get_member_list_sorted(member_list):
  return sorted(member_list, key = lambda m :(-m["org_member"], m["org_deactivated"], m["org_unconfirmed"], m["org_member_type"], m["fullName"]))

def print_members_list_texttable(member_list):
  table = Texttable()
  table.header(["org member type", "full name", "username", "org deactivated", "org unconfirmed", "# boards readable", "# boards deactivated"])
  table.set_cols_width([10, 30, 30, 15, 11, 10, 11])

  for m in member_list:
    table.add_row([m["org_member_type"], 
                 m["fullName"], 
                 m["username"], 
                 str(m["org_deactivated"]), 
                 str(m["org_unconfirmed"]), 
                 len([b for b in m["boards_with_membership_info"] if b["board_readable_to_user"]]),
                 len([b for b in m["boards_with_membership_info"] if b["board_deactivated"]])])

  print table.draw()

def print_boards_for_member_header(member):
  print "org member type: %s" % member["org_member_type"]
  print "full name: %s" % member["fullName"]
  print "username: %s" % member["username"]
  print "org deactivated: %s" % member["org_deactivated"]
  print "unconfirmed: %s " % member["org_unconfirmed"]
  print ''

def print_boards_for_member_texttable(member):
  table = Texttable()
  boards_with_membership_info_sorted = sorted(member["boards_with_membership_info"], key = lambda b :(-(b["board_readable_to_user"]), b["name"]))
  table.header(["readable?", "Name", "URL", "member type", "board unconfirmed", "board deactivated"])
  table.set_cols_width([10, 30, 30, 10, 11, 11])
  for board_with_membership_info in boards_with_membership_info_sorted:
    table.add_row([str(board_with_membership_info["board_readable_to_user"]),
                  board_with_membership_info["name"],
                  board_with_membership_info["shortUrl"],
                  board_with_membership_info["board_member_type"],
                  str(board_with_membership_info["board_unconfirmed"]),
                  str(board_with_membership_info["board_deactivated"])])

  print table.draw()

def print_specific_member(username, member_list):
  members = [m for m in member_list if m["username"] == username]
  if members:
    member = members[0]
    print_boards_for_member_header(member)
    print_boards_for_member_texttable(member)
  else:
    print "There was no member found with that username who is a member of the organization or any boards within the organization."


# org member type, full name, username, org deactivated, unconfirmed, # boards visible, # boards deactivated

def main():
  org_memberships = get_org_memberships(id_org)
  org_memberships_normal_and_admin = get_org_members_normal_and_admin(org_memberships)
  get_org_memberships_deactivated = get_org_members_deactivated(org_memberships)
  org_boards = get_org_boards(id_org)
  member_list = get_member_list_from_org_membership(org_memberships)


  for board in org_boards:
    # quick note about performance and optimization here. We're getting the detailed board membership for each board. We
    # *could get that information in get_org_boards if we asked for memberships=all, but there's not a way to get member info,
    # e.g. member fullName and username, in that call. We'd have to make a separate call for each board member that wasn't
    # also an org member. Arguably that's probably more effecient in the long run, but also more complex.
    board_memberships = get_board_memberships(board["id"])
    for board_membership in board_memberships:
      add_board_member_to_member_list(board_membership, board, member_list)


  sorted_member_list = get_member_list_sorted(member_list)
  
  print_everything = not args.user and not args.summary

  if args.user:
    print_specific_member(args.user, sorted_member_list)
  else:
    if args.summary or args.all or print_everything:
      print_members_list_texttable(sorted_member_list)

    if args.all or print_everything:
      for member in sorted_member_list:
        print ''
        print_boards_for_member_header(member)
        print_boards_for_member_texttable(member)


if __name__ == "__main__":
    main()


