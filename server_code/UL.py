import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import os
import heapq
import time

manifest_path = 'ShipCase2.txt'

# Inputs will be list of containers to unload, represented as tuple of starting position
# and number of containers to load
unload_list = []
load_list = 0
load_names = []

rows = 10
cols = 12
board = []
final_descriptions = []
operation_list = []
finished_unload = False

@anvil.server.callable
def load_unload():
    global rows
    global cols
    global board
    global final_descriptions
    global operation_list
    global finished_unload
    global manifest_path
    
    global unload_list
    global load_list
    global load_names

    for row in app_tables.input_manifest.search():
      manifest_content = row['media_obj'].get_bytes().decode("utf-8")
      manifest_path = row['media_obj'].name
      
      print(manifest_path)
      
    file_path = "unload_list.txt"
    row = app_tables.data.get(name=file_path)
    file_media = row['media_obj']
  
    file_content = file_media.get_bytes().decode("utf-8")
  
    lines = file_content.split('\n')
    for line in lines:
      if len(lines) == 1 and line == "":
        break;
      container = line.split(' ')
      unload_list.append((int(container[0]), int(container[1])))

    file_path = "load_list.txt"
    row = app_tables.data.get(name=file_path)
    file_media = row['media_obj']
  
    file_content = file_media.get_bytes().decode("utf-8")
  
    load_list = len(file_content.split('\n'))
    
    lines = file_content.split('\n')
    for line in lines:
      line = line.split(' ')
      load_names.append(line[0])
    if load_names[0] == "":
      load_list = 0
      load_names = []
    
    # 2-D list of ints to represent starting board
    board =  [ [0] * cols for _ in range(rows)]
    # 2-D list of strings to track manifest descriptions
    descriptions = [ ['UNUSED'] * cols for _ in range(rows)]

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

    print(manifest_path +"'s ship requests our balancing routine:")
    print('Need to load:', load_list, 'containers')
    print('Need to unload containers at:')
    print(unload_list)
    print()
    print_board(board)
    start_time = time.time()
    print()

    load_names.reverse()
    final_board = load_unload_ship(board)
    final_descriptions = final_descriptions[:-2]
    write_to_file(final_descriptions, final_board)
    write_list_to_file()
    end_time = time.time()
    print("Time taken:", '%.2f'%(end_time-start_time),"seconds")


# Function to print our ship bay with 6 spaces horizontally between cells to account for 5 digit weight cap
# 0 is unused
# -1 is NAN
# >0 is unempty container 
def print_board(b):
  # Printing in reverse order since [01,01] is defined as the bottom left corner
  b.reverse()
  print('\n'.join([''.join(['{:6}'.format(item) for item in row]) for row in b]))
  b.reverse()

def print_descriptions(d):
  d.reverse()
  print('\n'.join([''.join(['{:8}'.format(item) for item in row]) for row in d]))
  d.reverse()

# Performs an in line swap between two positions on a given board 
def swap(this_board, a, b):
  x = this_board[a[0]][a[1]]
  this_board[a[0]][a[1]] = this_board[b[0]][b[1]]
  this_board[b[0]][b[1]] = x

# Given a container position and current board, returns a list of tuples containing all the possible cells it can be moved to
def open_slots(this_board, container):
  # Starts with indices of closest positions and expands outwards
  list_ind = []
  slots = []
  temp = [*zip(*this_board)]
  x = container[1]
  y = 1
  while len(list_ind) != cols-1:
    if x-y < 0:
      list_ind.append(x+y)
    elif x+y > cols-1:
      list_ind.append(x-y)
    else:
      list_ind.append(x-y)
      list_ind.append(x+y)
    y += 1
  
  # Finds the first 0 in column indices in list_ind
  slots = []
  temp = [*zip(*this_board)]
  for i in list_ind:
    try:
      dest_row = temp[i].index(0)
      slots.append((dest_row, i))
    except ValueError as e:
      continue
  return slots

# Returns the active list of exposed/grabbable containers with their positions in a given board
def container_list(this_board):
  all_containers = [(i,j) for i, x in enumerate(this_board) for j, y in enumerate(x) if y>0]
  trimmed = [a for a in all_containers if a[0]<rows-1]
  return [z for z in trimmed if this_board[z[0]+1][z[1]] == 0]
   
# Returns true if we unloaded and loaded all items, false otherwise
def finished(unloads, load_count):
  return len(unloads) == 0 and load_count == 0

# Returns a list of tuples of all loadable slots
def open_load_slots(this_board):
  list_open = []
  temp = [*zip(*this_board)]
  for col, _ in enumerate(temp):
    try:
      dest_row = temp[col].index(0)
      list_open.append((dest_row, col))
    except ValueError as e:
      continue
  return list_open

# Returns the manhattan distance to the closest open slot to load a container
def closest_load_dist(this_board):
  list_open = open_load_slots(this_board)
  distances = [manhat(x,(rows-2,0)) for x in list_open]
  return min(distances)

# Our heuristic is the sums of manhattan distances between containers to unload and the virtual pink cell  
# added with the manhattan distances of containers to be loaded and the closest current loading spot
def get_h(b):
  h = 0
  for container in b.unloads_left:
    h = h + 15 + manhat(container, (rows-2,0))
  return h + b.loads_left*(15 + closest_load_dist(b.board))

# Prints the path trace for balance solution and the estimated time cost to perform the balance
def print_path(current_board):
  pickups = []
  movetos = []
  locations = []

  current = current_board
  while current is not None:
    pickups.append(current.crane_pickup_pos)
    movetos.append(current.crane_moveto_pos)
    locations.append(current.location)
    current = current.prev_board
  pickups.pop()
  movetos.pop()
  locations.pop()
  pickups = pickups[::-1]
  movetos = movetos[::-1]
  locations = locations[::-1]

  time_estimate = 0
  last_pos = (rows-2,0)
  last_loc = 'Dock'
  loads = load_list
  unloads = len(unload_list)
  trace_board = [row[:] for row in board]
  # print('Started at Dock')
  for p, m, l in zip(pickups, movetos, locations):
    # Loaded Container
    if last_loc == 'Dock' and loads > 0:
      # print('Loaded container from Dock to', m)
      loads -= 1
      time_estimate = time_estimate + 15 + manhat(p, m)
      trace_board[m[0]][m[1]] = 99999
      final_descriptions[m[0]][m[1]] = load_names.pop()
      last_pos = m
      last_loc = l
      temp_s = temp_s = '' + str(8) + ' ' + str(0) + ' ' + str(m[0]) + ' ' + str(m[1]) + ' '+ final_descriptions[m[0]][m[1]] + ' L'
      operation_list.append(temp_s)
      # print('Total time so far:', time_estimate)
    # No more loads, simply moved back to Bay
    elif last_loc == 'Dock' and loads == 0:
      # print('Moved crane from Dock to Bay')
      time_estimate += 15
      last_pos = m
      last_loc = l
      # print('Total time so far:', time_estimate)
    # Unloaded Container
    elif last_loc == 'Bay' and l == 'Dock' and unloads > 0:
      # print('Moved crane from', last_pos, 'to', p)
      time_estimate += manhat(last_pos, p)
      # print('Unloading container at', trace_board[p[0]][p[1]], 'at', p)
      trace_board[p[0]][p[1]] = 0
      temp_s = temp_s = '' + str(p[0]) + ' ' + str(p[1]) + ' ' + str(8) + ' ' + str(0) + ' '+ final_descriptions[p[0]][p[1]] + ' U'
      operation_list.append(temp_s)
      final_descriptions[p[0]][p[1]] = 'UNUSED'
      time_estimate = time_estimate + manhat(p, m) + 15
      last_pos = m
      last_loc = l
      # print('Total time so far:', time_estimate)
    # No more unloads, simply moved to Dock
    elif last_loc == 'Bay' and l == 'Dock' and unloads == 0:
      # print('Moved crane from Bay to Dock')
      time_estimate += 15
      last_pos = m
      last_loc = l
      # print('Total time so far:', time_estimate)
    # Swapped Container
    else:
      # print('Moved crane from', last_pos, 'to', p)
      time_estimate += manhat(last_pos, p)
      # print('Moved container', trace_board[p[0]][p[1]], 'at', p, 'to', m)
      temp_s = '' + str(p[0]) + ' ' + str(p[1]) + ' ' + str(m[0]) + ' ' + str(m[1]) + ' '+ final_descriptions[p[0]][p[1]] + ' M'
      operation_list.append(temp_s)
      time_estimate += manhat(p, m)
      swap(trace_board, p, m)
      swap(final_descriptions, p, m)
      last_pos = m
      last_loc = l
      # print('Total time so far:', time_estimate)
  if last_loc == 'Dock':
    # print('Ended at Dock, estimated time for balance list of operations is', time_estimate, 'minutes')
    pass
  else:
    # print('Moved crane from', last_pos, 'to', (rows-2,0))
    time_estimate = time_estimate + manhat(last_pos, (rows-2,0)) + 15
    # print('Moved crane to Dock, estimated time for balance list of operations is', time_estimate, 'minutes')
  return trace_board

# Board class to track manifest states in the astar balancing algorithm
class Board():
  def __init__(self, board=None, prev_board=None):
    self.board = board
    self.prev_board = prev_board

    self.g = 0
    self.h = 0
    self.f = 0

    self.unloads_left = []
    self.loads_left = 0

    self.location = ''

    self.crane_pickup_pos = ()
    self.crane_moveto_pos = ()

  def __eq__(self,other):
    return self.board == other.board and self.unloads_left == other.unloads_left and self.loads_left == other.loads_left and self.location == other.location

  def __lt__(self, other):
    if self.f == other.f:
      return self.h < other.h
    else:
      return self.f < other.f

  def __gt__(self, other):
    if self.f == other.f:
      return self.h > other.h
    else:
      return self.f > other.f
  
  def __repr__(self):
      return f"g: {self.g} h: {self.h} f: {self.f}"

# A star searching algorithm that attempts to load and unload containers in the least time
def load_unload_ship(init_board):

  global finished_unload

  start_board = Board(init_board, None)
  start_board.unloads_left = unload_list
  start_board.loads_left = load_list
  start_board.location = 'Dock'
  start_board.g = 0
  start_board.h = get_h(start_board)
  start_board.f = start_board.g + start_board.h*10
  start_board.crane_pickup_pos = (rows-2,0)
  start_board.crane_moveto_pos = (rows-2,0)
  

  min_diff = start_board

  open_list = []
  closed_list = []

  heapq.heapify(open_list) 
  heapq.heappush(open_list, start_board)

  outer_iterations = 0
  max_iterations = 20000

  while len(open_list) > 0:
    outer_iterations += 1

    current_board = heapq.heappop(open_list)
    closed_list.append(current_board)
    # print("Expanding Board:")
    # print(current_board)
    # print_board(current_board.board)
    if outer_iterations > max_iterations:
      print('2FAILURE: Unable to find load/unload operation list in time')
      # print_path(min_diff)
      print()
      print("Final manifest preview shown below:\n")
      print_board(min_diff.board)
      return

    if finished(current_board.unloads_left, current_board.loads_left):
      if sum(current_board.board[rows-1]) == 0:
        print('SUCCESS: Load/Unload operation list found!')
        print("Boards expanded: "+ str(outer_iterations))
        final_board = print_path(current_board)
        print()
        print("Final manifest preview shown below:\n")
        print_board(current_board.board)
        return final_board

    if current_board.f < min_diff.f:
      min_diff = current_board

    if current_board.location == 'Dock':
      # Expanding to all possible load positions
      if current_board.loads_left > 0:
        for possible_move in open_load_slots(current_board.board):
          temp_board = [row[:] for row in current_board.board]
          temp_board[possible_move[0]][possible_move[1]] = 99999
          new_board = Board(temp_board, current_board)
      
          if len([closed_child for closed_child in closed_list if closed_child == new_board]) > 0:
            continue
          new_board.loads_left = current_board.loads_left - 1
          new_board.unloads_left = current_board.unloads_left[:]
          new_board.location = 'Bay'

          new_board.g = current_board.g + 1 + manhat(current_board.crane_moveto_pos, (rows-2,0)) + 15 + manhat((rows-2,0), possible_move)
          new_board.h = get_h(new_board)
          new_board.f = new_board.g + new_board.h

          new_board.crane_pickup_pos = (rows-2,0)
          new_board.crane_moveto_pos = possible_move

          if len([open_node for open_node in open_list if new_board == open_node and new_board.g > open_node.g]) > 0:
            continue
          heapq.heappush(open_list, new_board)
      # No more containers to load, moving crane back to Bay without a load
      else:
        temp_board = [row[:] for row in current_board.board]
        new_board = Board(temp_board, current_board)

        if len([closed_child for closed_child in closed_list if closed_child == new_board]) > 0:
          continue
        new_board.loads_left = current_board.loads_left
        new_board.unloads_left = current_board.unloads_left[:]
        new_board.location = 'Bay'

        new_board.g = current_board.g + 1 + 15
        new_board.h = get_h(new_board)
        new_board.f = new_board.g + new_board.h

        new_board.crane_pickup_pos = (rows-2,0)
        new_board.crane_moveto_pos = (rows-2,0)

        if len([open_node for open_node in open_list if new_board == open_node and new_board.g > open_node.g]) > 0:
          continue
        heapq.heappush(open_list, new_board)
    # current_board.location == 'Bay'
    else:
      # If still need to unload, we expand all exposed containers
      if len(current_board.unloads_left) > 0:
        for my_container in container_list(current_board.board):
          # Exposed container is in unload_list, so we unload
          if my_container in current_board.unloads_left:
            temp_board = [row[:] for row in current_board.board]
            temp_board[my_container[0]][my_container[1]] = 0
            new_board = Board(temp_board, current_board)

            if len([closed_child for closed_child in closed_list if closed_child == new_board]) > 0:
              continue
            new_board.unloads_left = current_board.unloads_left[:]
            new_board.unloads_left.remove(my_container)
            new_board.loads_left = current_board.loads_left
            new_board.location = 'Dock'

            new_board.g = current_board.g + 1 + manhat(current_board.crane_moveto_pos, (rows-2,0)) + 15
            new_board.h = get_h(new_board)
            new_board.f = new_board.g + new_board.h

            new_board.crane_pickup_pos = my_container
            new_board.crane_moveto_pos = (rows-2,0)

            if len([open_node for open_node in open_list if new_board == open_node and new_board.g > open_node.g]) > 0:
              continue
            heapq.heappush(open_list, new_board)
          # Exposed container is not in unload_list, so we expand to every open slot
          else:
            if finished_unload == True:
              continue
            for possible_move in open_slots(current_board.board, my_container):
              temp_board = [row[:] for row in current_board.board]
              swap(temp_board, my_container, possible_move)
              new_board = Board(temp_board, current_board)

              if len([closed_child for closed_child in closed_list if closed_child == new_board]) > 0:
                continue

              new_board.unloads_left = current_board.unloads_left[:]
              new_board.loads_left = current_board.loads_left
              new_board.location = 'Bay'

              new_board.g = current_board.g + 10 + manhat(current_board.crane_moveto_pos, my_container) + manhat(my_container, possible_move)
              new_board.h = get_h(new_board)
              new_board.f = new_board.g + new_board.h
              
              new_board.crane_pickup_pos = my_container
              new_board.crane_moveto_pos = possible_move

              if len([open_node for open_node in open_list if new_board == open_node and new_board.g > open_node.g]) > 0:
                continue
              heapq.heappush(open_list, new_board)
      # No more containers to unload, moving crane to Dock without an unload
      else:
        finished_unload = True
        temp_board = [row[:] for row in current_board.board]
        new_board = Board(temp_board, current_board)

        if len([closed_child for closed_child in closed_list if closed_child == new_board]) > 0:
          continue
        new_board.loads_left = current_board.loads_left
        new_board.unloads_left = current_board.unloads_left[:]
        new_board.location = 'Dock'

        new_board.g = current_board.g + 1 + 15
        new_board.h = get_h(new_board)
        new_board.f = new_board.g + new_board.h

        new_board.crane_pickup_pos = (rows-2,0)
        new_board.crane_moveto_pos = (rows-2,0)

        if len([open_node for open_node in open_list if new_board == open_node and new_board.g > open_node.g]) > 0:
          continue
        heapq.heappush(open_list, new_board)

  print('1FAILURE: Unable to find load/unload operation list')
  # print("Boards expanded: "+ str(outer_iterations))
  # print_path(min_diff)
  print()
  print("Final manifest preview shown below:\n")
  print_board(min_diff.board)
  return

def manhat(start, end):
  return abs(start[0]-end[0]) + abs(start[1]-end[1])

def write_to_file(d, b):
  lines = []
  for i, x in enumerate(d):
    for j, y in enumerate(x):
      if b[i][j] < 0:
        b[i][j] = 0
      line = '[0' + str(i+1) + ',' + ('0' + str(j+1))[-2:] + '], {' + ('0000' + str(b[i][j]))[-5:]+ '}, ' + y
      lines.append(line)

  output_manifest_path = manifest_path + '-OUTBOUND.txt'
  file_contents = ""
  new_line = ""
  for line in lines:
    file_contents = file_contents + new_line + line
    new_line = "\n"
          
  file_contents = file_contents.encode()      # String as bytes
  output_manifest_media = anvil.BlobMedia(content_type="text/plain", content=file_contents, name=output_manifest_path)
  app_tables.output_manifest.delete_all_rows()
  app_tables.output_manifest.add_row(name=output_manifest_path, media_obj=output_manifest_media)

def write_list_to_file():
    output_path = "operation_list.txt"
    file_contents = ""
    new_line = ""
    for operation in operation_list:
      file_contents = file_contents + new_line + operation
      new_line = "\n"
         
    file_contents = file_contents.encode()      # String as bytes
    output_media = anvil.BlobMedia(content_type="text/plain", content=file_contents, name=output_path)
    row = app_tables.data.get(name=output_path)
    row['media_obj'] = output_media