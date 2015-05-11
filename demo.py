### An intro to the Trello API ###
#
# This is a basic intro to using the Trello API. I'm using Python, but the basic concepts
# should work in any language. 
#
# This file is meant to be read from top to bottom for someone who is brand new to interacting
# with the Trello API. To run the Python code, type `python demo.py` from the command line.
#
# The 'requests' Python library make it easy to visually see
# how we're interacting with API.
#
###############

import requests           # a 3rd party library. I installed via `pip install requests`
import json               # all responses from Trello come back as JSON, so have your favorite JSON library handy
from pprint import pprint # this is a handy utility for printing dictionaries in a human readable way

### Getting an API Key and Token
#
# The first thing we're going to want to do is get an API key and token. I'm taking an 
# admittedly naive approach, where I'm assuming you're planning on simply running scripts
# against your own Trello account. For public uses, you'd want to use OAuth, which I'm not
# going to go into here
#
# NB: You might want a settings.py file so that you can store your key and token outside of version control
#
# The key tells Trello which developer's code is trying to run against the API
#
# To start, in your browser, log in as the account you want to use aginst the Trello API
# go to: https://trello.com/1/appKey/generate
# copy the key here or to your settings file

key = ''
# if you're storing your key in this file, you don't need the following three lines
if not key:
  from settings import trello_key 
  key = trello_key

# The token tells Trello which user has authroized access to their accounts. To rehash, the
# key tells Trello who the developer is and the token tells Trello whose account we're accessing.
# 
# In your browser, go to:
#
#   https://trello.com/1/authorize?response_type=token&key=[[  YOUR KEY HERE ]]&scope=read,write&expiration=never&name=Trello+API+Demo
#
#   Note that you can change the scope, expiration, and name (the name is used to identify who you gave access to at trello.com/your/account )
#   You'll get a token back in your browser when you click allow. Paste that below or in a separate file.

token = ''
# if you're storing your token in this file, you don't need the following three lines
if not token:
  from settings import trello_token 
  token = trello_token

# We'll use the key and token in subsequent requests to the Trello API
#
###################################


### How to make requests to the Trello API ###
#
# All of the public documented Trello API methods:
#
#     https://trello.com/docs/api/index.html
#
# Using the documented API methods, we can build out a request by piecing
# together the various parts of the URL. 
#
# For example, if I want to get a list of my boards, documented at https://trello.com/docs/api/member/index.html#get-1-members-idmember-or-username-boards,
# I would make a GET request to the following URL
#
#   base url: https://trello.com/1/
#        
#              +
#   members
#
#              +
#
#   idMember or username (NB: you can use 'me' as a substitute for yourself)
#
#              +
#
#   boards
#
#              =
#
#   https://trello.com/1/members/me/boards
#
#
#
# Go ahead and paste https://trello.com/1/members/me/boards in your browser, which will make
# a GET request to the Trello API and return a JSON array of your boards.
#   PRO TIP: Install the JSONView Chrome extension to easily view the result. 
#
# 
# For each request, you need to do two things:
# 
#   1) Identify which HTTP method you're going to use: GET, PUT, POST, or DELETE
#        - NB: You can think of PUT as shorthand for 'update' (something that already exists) 
#              and POST as shorthand for 'insert' (something that's being added for the first time).
#              HTTP pedants might balk at that, but it will work for us.
#   2) Piece together the URL you want to target
#
# You'll probably want to create helper methods/classes for your particular environment to make that
# a bit easier. For now, I'll piece stuff together manually. For an example of a small python library that 
# does some of this for you, see https://developers.kilnhg.com/Code/Trello/Group/TrelloSimple/Files/trelloSimple.py?rev=eeef45bd880a&nr=
#
# Let's make some requests!
#
#####################

### Your first GET request to the Trello API ###
#
# We're going to make a GET request to the Trello API and print out a list of the boards
# to which we belong. It's documented here: https://trello.com/docs/api/member/index.html#get-1-members-idmember-or-username-boards
#
# The base url for every request is the same
base = 'https://trello.com/1/'

# Build out the URL based on the documentation
boards_url = base + 'members/me/boards'

# Let's store our API key and token as parameters
params_key_and_token = {'key':key,'token':token}

# Since we only want the name of the board, let's supply the 'fields' argument as well. We're also going to 
# ask for lists, to be used later.
arguments = {'fields': 'name', 'lists': 'open'}

# The requests library has separate methods for get, put, post, and delete. We need a GET here.
# We need to provide the URL we want to access, the key and token (params_key_and_token) as params, as well as
# any arguments (arguments) as data.
response = requests.get(boards_url, params=params_key_and_token, data=arguments)

# We should pause here and point out that the requests library is making everying incredibly
# easy for us. We're able to work in native python dictionaries and requests is automatically
# form-encoding our 'arguments' dictionary when the request is made. This is quite handy
# and lets us get right to working with the Trello API.
#
# If you're making your own script, you might check out query_trello in 
# trello_helper.py, which wraps up the last few lines of code in a repeatable 
# fashion.

# Since we're using requests, there's a json() method for decoding the response. If you're not using 
# requests or are using a different language, you may need to use your favorite JSON library to deserialize
# the content of the response into a native dictionary.
#
# The following will give us an array of dictionaries
response_array_of_dict = response.json()

# Let's go ahead and iterate through the list of boards and print the name of each board
for board in response_array_of_dict:
  print board['name']

# How about that! Now let's move on to something a bit more complicated
#
###########################



### Adding a card to the welcome board #######################
#
# Now that we've comfortable making a request, let's try adding a card to the Welcome Board.
#
# This is documented here: https://trello.com/docs/api/card/index.html#post-1-cards
#
# NB: This part assumes you have a board named "Welcome Board", which is added when you sign 
#     up for Trello, but if you removed or renamed it, go ahead and add one to the account 
#     you're testing with.
#
# Since we already have a list of boards, let's iterate through that list and find the welcome board

for board in response_array_of_dict:
  # Look for the board name that matches 'Welcome Board'
  if board['name'] == 'Welcome Board':
    # Before we go further, let's go ahead and build our URL, based on https://trello.com/docs/api/card/index.html#post-1-cards
    cards_url = base + 'cards'

    # Back when we originally queried the Trello API, we asked it to include the lists on the board.
    # We need a list to add a card, so let's grab the id of the first list:
    id_list = board['lists'][0]['id']

    # Let's provide a name and description for the card
    name = 'Card via the API'
    description = 'I made this card using the Trello API :fist:'

    # These values need to be put into a dictionary, which requests will form-encode for us
    arguments = {'name': name, 
                 'desc': description,
                 'idList' : id_list}

    # Since this particular method uses POST, we're going to need to use requests.post
    response = requests.post(cards_url, params=params_key_and_token, data=arguments)

    # When we POST a new card to Trello, the API will responsd with json data about the
    # the new card. Let's pretty print the response and take a look at it.
    pprint(response.json())

# That's pretty much it. Identify what you want to do in Trello, find the right API method,
# write some for loops, and you're done.
#
# For the full documentation, see https://trello.com/docs/























