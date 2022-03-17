import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from anvil.tables import app_tables


# This is a server module. It runs on the Anvil server,
# rather than in the user's browser.
#
# To allow anvil.server.call() to call functions here, we mark
# them with @anvil.server.callable.
# Here is an example - you can replace it with your own:
#
@anvil.server.callable
def say_hello(): 
  print("Hello!")
  
@anvil.server.callable
# Prints out contents of the manifest
def print_from_file():
  for row in app_tables.my_files.search():
    print(row['media_obj'].get_bytes())


  



