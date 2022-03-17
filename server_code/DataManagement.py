import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from anvil.tables import app_tables
import os
import heapq
import time

# Moving manhattanly between cells takes 1 minute
# Transferring from or to a truck takes 2 minutes
# Transferring between ship and buffer takes 15 minutes
# While loading only, the ship’s operation range is technically expanded to 10 x 12, where the extra 2 rows can be used to temporarily stack containers

# 12 x 8 grid
# 24 x 4 buffer


manifest_path = 'ShipCase4.txt'
rows = 8
cols = 12
partitions = []
board = []
final_descriptions = []

@anvil.server.callable
def load_manifest_grid():
    
    global rows
    global cols
    global board
    global partitions
    global final_descriptions
    global manifest_path
    
    for row in app_tables.input_manifest.search():
      manifest_content = row['media_obj'].get_bytes().decode("utf-8")
      manifest_path = row['media_obj'].name
      
    # 2-D list of ints to represent starting board
    board =  [ [0] * cols for _ in range(rows)]
    # 2-D list of strings to track manifest descriptions
    descriptions = [ [''] * cols for _ in range(rows)]

#     f = open(manifest_path, 'r')
#     lines = f.readlines()
    lines = manifest_content.split('\n')

    # Parsing the input file, manifest, into a 2-D list of ints holding the weights of the containers 
    for line in lines:
        if line[18:].strip() == 'NAN':
            board[int(line[1:3])-1][int(line[4:6])-1] = -1
            descriptions[int(line[1:3])-1][int(line[4:6])-1] = 'NAN'
        elif line[18:].strip() == 'UNUSED':
            descriptions[int(line[1:3])-1][int(line[4:6])-1] = 'UNUSED'
        # elif line[10:15] == '00000': #TODO empty container case
        # thinking about making them 1, or even 0.01, so they still count as untraversable blocks to astar and we can still round their weight to 0
        else:
            container_row = int(line[1:3])-1
            container_col = int(line[4:6])-1
            container_weight = int(line[10:15])
            board[container_row][container_col] = container_weight
            descriptions[container_row][container_col] = line[18:].strip()

    final_descriptions = [row[:] for row in descriptions]
    
    return final_descriptions, board
    
    
    
    # board (starting weights positions of ship)
    # descriptions (starting description positions of ship)
    # final_board (ending weights positions of ship)
    # final_descriptions (ending description positions of ship)
    
@anvil.server.callable
def write_unload_containers(unload_list):
  
    output_path = "unload_list.txt"
    file_contents = ""
    new_line = ""
    for container in unload_list:
      file_contents = file_contents + new_line + str(container[0]) + " " + str(container[1]) + " " + container[2]
      new_line = "\n"
         
    file_contents = file_contents.encode()      # String as bytes
    output_media = anvil.BlobMedia(content_type="text/plain", content=file_contents, name=output_path)
    row = app_tables.data.get(name=output_path)
    row['media_obj'] = output_media
    
@anvil.server.callable
def write_load_containers(load_list):
  
    output_path = "load_list.txt"
    file_contents = ""
    new_line = ""
    for container in load_list:
      file_contents = file_contents + new_line + container
      new_line = "\n"
         
    file_contents = file_contents.encode()      # String as bytes
    output_media = anvil.BlobMedia(content_type="text/plain", content=file_contents, name=output_path)
    row = app_tables.data.get(name=output_path)
    row['media_obj'] = output_media
    
@anvil.server.callable
def load_load_textfile():
  
  file_path = "load_list.txt"
  row = app_tables.data.get(name=file_path)
  file_media = row['media_obj']
  
  file_content = file_media.get_bytes().decode("utf-8")
  
  lines = file_content.split('\n')
  
  if len(lines) == 1 and lines[0] == "":
    lines = []
  return lines

@anvil.server.callable
def load_unload_textfile():
  
  file_path = "unload_list.txt"
  row = app_tables.data.get(name=file_path)
  file_media = row['media_obj']
  
  file_content = file_media.get_bytes().decode("utf-8")
  
  lines = file_content.split('\n')
  
  container_names = []
  for line in lines:
    if len(lines) == 1 and line == "":
      break;
    line = line.split(" ")
    container_names.append(line[2])
    
  return container_names

@anvil.server.callable
def get_file_from_client(file):
  print(file.name)
  # Delete file currently in db before adding new file to db
  app_tables.input_manifest.delete_all_rows()
  app_tables.input_manifest.add_row(name=file.name, media_obj=file)
  
@anvil.server.callable
def get_balance_step(step_number):
  
  file_path = "operation_list.txt"
  row = app_tables.data.get(name=file_path)
  file_media = row['media_obj']
  
  file_content = file_media.get_bytes().decode("utf-8")
  
  lines = file_content.split('\n')
  
  for index_line in range(len(lines)):
    # if the operation list is empty
    if index_line == 0 and lines[0] == "":
      return []
    words = lines[index_line].split(" ")
    if index_line+1 == step_number:
      return [(int(words[0]), int(words[1])), (int(words[2]), int(words[3])), words[4]]
    
  return []