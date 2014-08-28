# Trello API Demo

This is meant to give you a basic demo of the [Trello API](https://trello.com/docs). I'm assuming
the reader knows a little bit about writing code, but may be new to interacting with a web API. If
you're looking to write scripts against your Trello account, this may be a good place to start.

I chose Python as a starting point because it's quite simple to read without getting lost in 
formatting HTTP connections and parsing responses. We let the 
[`requests`](http://docs.python-requests.org/) library do most of the heavy lifting so we can
focus on writing procedural code.

## How this works

Start with `demo.py`. You can read it from top to bottom to learn how to interact with the Trello API.
You can even run the code via `python demo.py`, but if you're just reading through it to learn how to
use the Trello API, you of course don't need to run it.

I made other `demo_` files for specific use cases (well, one more for now). They assume you've read
`demo.py`.