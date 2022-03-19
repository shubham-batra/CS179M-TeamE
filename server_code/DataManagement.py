import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from anvil.tables import app_tables
from datetime import datetime
import pytz

@anvil.server.callable
def load_manifest_grid():
    
    rows = 8
    cols = 12
    partitions = []
    board = []
    final_descriptions = []
    manifest_path = ""
    
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
def load_load_textfile_containers():
  
  file_path = "load_list.txt"
  row = app_tables.data.get(name=file_path)
  file_media = row['media_obj']
  
  file_content = file_media.get_bytes().decode("utf-8")
  
  lines = file_content.split('\n')
  
  load_containers = []
  for line in lines:
    if len(lines) == 1 and line == "":
      break;
    line = line.split(" ")
    load_containers.append(line[0])
    
  return load_containers

@anvil.server.callable
def load_unload_textfile_containers():
  
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
def get_operation_step(step_number):
  
  file_path = "operation_list.txt"
  row = app_tables.data.get(name=file_path)
  file_media = row['media_obj']
  
  file_content = file_media.get_bytes().decode("utf-8")
  
  lines = file_content.split('\n')
  
  # Popping the estimated time
  lines.pop(0)
  for index_line in range(len(lines)):
    # if the operation list is empty
    if index_line == 0 and lines[0] == "":
      return []
    words = lines[index_line].split(" ")
    if index_line+1 == step_number:
#       return [(int(words[0]), int(words[1])), (int(words[2]), int(words[3])), words[4]]
      return [(int(words[0]), int(words[1])), (int(words[2]), int(words[3])), words[4], words[5]]
    
  return []

@anvil.server.callable
def get_est_time():
  
  file_path = "operation_list.txt"
  row = app_tables.data.get(name=file_path)
  file_media = row['media_obj']
  
  file_content = file_media.get_bytes().decode("utf-8")
  
  lines = file_content.split('\n')
  
  # Returning estimated time, should be in the first line
  return lines[0]

@anvil.server.callable
def load_load_textfile():
    
  file_path = "load_list.txt"
  row = app_tables.data.get(name=file_path)
  file_media = row['media_obj']
  
  file_content = file_media.get_bytes().decode("utf-8")
  
  lines = file_content.split('\n')
  
  load_list = []
  for line in lines:
    if len(lines) == 1 and line == "":
      break;
    line = line.split(" ")
    if len(line) == 1:
      line.append("")
    load_list.append([line[0], line[1]])
    
  return load_list

@anvil.server.callable
def write_load_container_weight(container_index, weight):
  
    load_list = load_load_textfile()
  
    output_path = "load_list.txt"
    file_contents = ""
    new_line = ""
    for index_container in range(len(load_list)):
      if index_container == container_index:
        file_contents = file_contents + new_line + load_list[index_container][0] + " " + str(weight)
      elif load_list[index_container][1] == "":
        file_contents = file_contents + new_line + load_list[index_container][0]
      else:
        file_contents = file_contents + new_line + load_list[index_container][0] + " " + load_list[index_container][1]
      new_line = "\n"
         
    file_contents = file_contents.encode()      # String as bytes
    output_media = anvil.BlobMedia(content_type="text/plain", content=file_contents, name=output_path)
    row = app_tables.data.get(name=output_path)
    row['media_obj'] = output_media

@anvil.server.callable
def update_user_textfile(username):
  output_path = "user.txt"
  file_contents = username
  file_contents = file_contents.encode()      # String as bytes
  output_media = anvil.BlobMedia(content_type="text/plain", content=file_contents, name=output_path)
  row = app_tables.data.get(name=output_path)
  row['media_obj'] = output_media
  
  
@anvil.server.callable
def load_user_textfile():
  file_path = "user.txt"
  row = app_tables.data.get(name=file_path)
  file_media = row['media_obj']
  
  file_contents = file_media.get_bytes().decode("utf-8")
    
  return file_contents

@anvil.server.callable
def load_input_manifest_path():
  for row in app_tables.input_manifest.search():
    manifest_path = row['media_obj'].name
  return manifest_path

@anvil.server.callable
def load_output_manifest_path():
  for row in app_tables.output_manifest.search():
    manifest_path = row['media_obj'].name
  return manifest_path

@anvil.server.callable
def load_output_manifest_media():
  for row in app_tables.output_manifest.search():
    media_obj = row['media_obj']
  return media_obj

@anvil.server.callable
def load_log_media():
  file_path = "log.txt"
  row = app_tables.data.get(name=file_path)
  file_media = row['media_obj']
  return file_media

@anvil.server.callable
def write_log(text):
  file_path = "log.txt"
  row = app_tables.data.get(name=file_path)
  file_media = row['media_obj']
  file_contents = file_media.get_bytes().decode("utf-8")
  
  tz_PST = pytz.timezone('America/Los_Angeles') 
  datetime_PST = datetime.now(tz_PST)
  time = datetime_PST.strftime("%d-%m-%Y %H:%M:%S")
  
  text = "\n[" + time + "] (" + load_user_textfile() + ") " + text
  file_contents = file_contents + text
  file_contents = file_contents.encode()      # String as bytes
  output_media = anvil.BlobMedia(content_type="text/plain", content=file_contents, name=file_path)
  row = app_tables.data.get(name=file_path)
  row['media_obj'] = output_media
  
@anvil.server.callable
def compile_UL_manifest():
  output_manifest_media = load_output_manifest_media()
  output_manifest_path = load_output_manifest_path()
  file_contents = output_manifest_media.get_bytes().decode("utf-8")
  
  operation_file_path = "operation_list.txt"
  row = app_tables.data.get(name=operation_file_path)
  operation_file_media = row['media_obj']

  load_list = load_load_textfile()
  
  operation_file_contents = operation_file_media.get_bytes().decode("utf-8")
  operation_file_contents = operation_file_contents.split('\n')
  
  file_contents_line_list = file_contents.split('\n')
  
  container_num = 0
  for line in operation_file_contents:
    line = line.split(' ')
    if line[5] == "L":
      
      for index, manifest_line in enumerate(file_contents_line_list):
        row = int(manifest_line[2:3]) - 1
        col = int(manifest_line[4:6]) - 1
        if row == int(line[2]) and col == int(line[3]):
          if load_list[container_num][1] == "":
            file_contents_line_list[index] = '[0' + str(row+1) + ',' + ('0' + str(col+1))[-2:] + '], {99999}, ' + load_list[container_num][0]
          else:
            file_contents_line_list[index] = '[0' + str(row+1) + ',' + ('0' + str(col+1))[-2:] + '], {' + ('0000' + str(load_list[container_num][1]))[-5:]+ '}, ' + load_list[container_num][0]
          container_num = container_num + 1          
  
  file_contents = ""
  new_line = ""
  for line in file_contents_line_list:
    file_contents = file_contents + new_line + line
    new_line = "\n"   
        
  file_contents = file_contents.encode()      # String as bytes
  output_manifest_media = anvil.BlobMedia(content_type="text/plain", content=file_contents, name=output_manifest_path)
  app_tables.output_manifest.delete_all_rows()
  app_tables.output_manifest.add_row(name=output_manifest_path, media_obj=output_manifest_media)
                                                                                          
  
  
  
  