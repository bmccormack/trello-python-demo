from requests import Request, Session
from settings import trello_key, trello_token
import requests
import json

def query_trello(method, url, data=None):
  BASE_URL = 'https://trello.com/1/'
  params_key_and_token = {'key':trello_key,'token':trello_token}
  url = BASE_URL + url
  s = Session()
  req = Request(method, url,
      data=data,
      params=params_key_and_token
  )

  prepped = s.prepare_request(req)

  resp = s.send(prepped)

  return resp