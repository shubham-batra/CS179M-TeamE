import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server

# This is a server module. It runs on the Anvil server,
# rather than in the user's browser.
#
# To allow anvil.server.call() to call functions here, we mark
# them with @anvil.server.callable.
# Here is an example - you can replace it with your own:
#
# @anvil.server.callable
# def say_hello(name):
#   print("Hello, " + name + "!")
#   return 42
#

# @anvil.server.callable
# def perform_backup():
#   print('hi')
#   pass

@anvil.server.callable
def get_backup_pressed():
  file_path = "backup_pressed.txt"
  row = app_tables.data.get(name=file_path)
  file_media = row['media_obj']

  file_contents = file_media.get_bytes().decode("utf-8")
    
  return int(file_contents)

@anvil.server.callable
def set_backup_pressed(flag):
  output_path = "backup_pressed.txt"
  file_contents = str(flag)
  file_contents = file_contents.encode()      # String as bytes
  output_media = anvil.BlobMedia(content_type="text/plain", content=file_contents, name=output_path)
  row = app_tables.data.get(name=output_path)
  row['media_obj'] = output_media
  
@anvil.server.callable
def write_backup(screen, step):
    output_path = "backup.txt"
    file_contents = '' + screen + '\n' + str(step)
         
    file_contents = file_contents.encode()      # String as bytes
    output_media = anvil.BlobMedia(content_type="text/plain", content=file_contents, name=output_path)
    row = app_tables.data.get(name=output_path)
    row['media_obj'] = output_media
    
@anvil.server.callable
def load_backup():
  file_path = "backup.txt"
  row = app_tables.data.get(name=file_path)
  file_media = row['media_obj']
  
  file_content = file_media.get_bytes().decode("utf-8")
  
  lines = file_content.split('\n')
  
#   Tuple containing (screen, step)
  return (lines[0], lines[1])


