import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from anvil.tables import app_tables
# Moving manhattanly between cells takes 1 minute
# Transferring from or to a truck takes 2 minutes
# Transferring between ship and buffer takes 15 minutes
# While loading only, the ship’s operation range is technically expanded to 10 x 12, where the extra 2 rows can be used to temporarily stack containers



# 12 x 8 grid
# 24 x 4 buffer

import os
import heapq
import time

manifest_path = 'ShipCase3.txt'
rows = 10
cols = 12
partitions = []
board = []
final_descriptions = []
operation_list = []

@anvil.server.callable
def balance():
    
    global rows
    global cols
    global board
    global partitions
    global final_descriptions
    global operation_list

    for row in app_tables.input_manifest.search():
      manifest_content = row['media_obj'].get_bytes().decode("utf-8")
      manifest_path = row['media_obj'].name
      
      print(manifest_path)
    
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
    
    partitions = partition_board(board)
    
    print(manifest_path +"'s ship requests our balancing routine:\n")
    print_board(board)
    start_time = time.time()
    print()
    final_board = balance_ship(board)
    final_descriptions = final_descriptions[:-2]
    write_to_file(final_descriptions, final_board)
    write_list_to_file()
    end_time = time.time()
    print("Time taken:", '%.2f'%(end_time-start_time),"seconds")

    # board (starting weights positions of ship)
    # descriptions (starting description positions of ship)
    # final_board (ending weights positions of ship)
    # final_descriptions (ending description positions of ship)

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

# Calculates an optimal balance partition of the ship using a Complete Greedy Algorithm
def partition_board(b):
    list_1 = []
    list_2 = []
    sum_list_1 = 0 
    sum_list_2 = 0
    all_containers = [b[i][j] for i, x in enumerate(b) for j, y in enumerate(x) if y>0]
    all_containers.sort(reverse=True)
    for container in all_containers:
        if sum_list_1 < sum_list_2:
            list_1.append(container)
            sum_list_1 += container
        else:
            list_2.append(container)
            sum_list_2 += container
    return list_1, list_2

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
   
# Returns true if a give board is balanced within 10% error, false otherwise
def balanced(this_board):
    left = [row[:cols//2] for row in this_board]
    right = [row[cols//2:] for row in this_board]
    sum_left = sum(map(sum,left))
    sum_right = sum(map(sum,right))
    percent_diff = abs(sum_left - sum_right)/max(sum_left, sum_right)
    return percent_diff < 0.1

# Our heuristic is the sum of horizontal distances of misplaced containers to (X,5) 
# if they are to the right and (X,6) if they are from the left
def get_h(this_board):
    # Calculating miplaced counts
    left = [row[:cols//2] for row in this_board]
    right = [row[cols//2:] for row in this_board]

    left_containers = [(i,j,left[i][j]) for i, x in enumerate(left) for j, y in enumerate(x) if y>0]
    right_containers = [(i,j,right[i][j]) for i, x in enumerate(right) for j, y in enumerate(x) if y>0]

    # Summing Euclidean distance of all misplaced containers considering both partitions
    dist_p1 = 0
    for container in left_containers:
        if container[2] not in partitions[0]:
            dist_p1 += (cols//2 - container[1])
    for container in right_containers:
        if container[2] not in partitions[1]:
            dist_p1 += (container[1] + 1)

    dist_p2 = 0
    for container in left_containers:
        if container[2] not in partitions[1]:
            dist_p2 += (cols//2 - container[1])
    for container in right_containers:
        if container[2] not in partitions[0]:
            dist_p2 += (container[1] + 1)

    return min(dist_p1, dist_p2)

# Prints the path trace for balance solution and the estimated time cost to perform the balance
def print_path(current_board):
    pickups = []
    movetos = []

    current = current_board
    while current is not None:
        pickups.append(current.crane_pickup_pos)
        movetos.append(current.crane_moveto_pos)
        current = current.prev_board
    pickups.pop()
    movetos.pop()
    pickups = pickups[::-1]
    movetos = movetos[::-1]

    time_estimate = 0
    last_pos = (rows-2,0)
    trace_board = [row[:] for row in board]

    # print('Started at pink virtual cell')
    for p, m in zip(pickups, movetos):
        # print('Moved crane from', last_pos, 'to', p)
        time_estimate += manhat(last_pos, p)
        # print('This took', time_estimate)
        # print('Moved container', descriptions[p[0]][p[1]], 'at', p, 'to', m)
        # temp_s = '' + str(p) + ' ' + str(m) + ' '+ final_descriptions[p[0]][p[1]]
        temp_s = '' + str(p[0]) + ' ' + str(p[1]) + ' ' + str(m[0]) + ' ' + str(m[1]) + ' '+ final_descriptions[p[0]][p[1]] + ' M'
        operation_list.append(temp_s)
        time_estimate += manhat(p, m)
        # print('This took', time_estimate)
        swap(trace_board, p, m)
        swap(final_descriptions, p, m)
        last_pos = m
        # print('Moved crane from', last_pos, 'to', (rows-2,0))
    time_estimate += manhat(last_pos, (rows-2,0))
    # print('Returned to and ended at pink virtual cell')
    # print('Estimated time for balance list of operations is', time_estimate, 'minutes')
    return trace_board

# Board class to track manifest states in the astar balancing algorithm
class Board():
    def __init__(self, board=None, prev_board=None):
        self.board = board
        self.prev_board = prev_board

        self.g = 0
        self.h = 0
        self.f = 0

        self.crane_pickup_pos = ()
        self.crane_moveto_pos = ()

    def __eq__(self,other):
        return self.board == other.board

    def __lt__(self, other):
        return self.f < other.f

    def __gt__(self, other):
        return self.f > other.f

    def __repr__(self):
        return f"g: {self.g} h: {self.h} f: {self.f}"

def reached_partition(b):
    left = [row[:cols//2] for row in b]
    left_containers = [left[i][j] for i, x in enumerate(left) for j, y in enumerate(x) if y>0]
    return left_containers == partitions[0] or left_containers == partitions[1]

# A star searching algorithm that attempts to balance a given initial board within 10% error
def balance_ship(init_board):
    start_board = Board(init_board, None)
    start_board.g = 0
    start_board.h = get_h(init_board)
    start_board.f = start_board.g + start_board.h
    start_board.crane_pickup_pos = (rows-2,0)
    start_board.crane_moveto_pos = (rows-2,0)

    min_diff = start_board

    open_list = []
    closed_list = []

    heapq.heapify(open_list) 
    heapq.heappush(open_list, start_board)

    outer_iterations = 0
    max_iterations = 500

    while len(open_list) > 0:
        outer_iterations += 1

        current_board = heapq.heappop(open_list)
        closed_list.append(current_board)
        # print("Expanding Board:")
        # print(current_board)
        # print_board(current_board.board)
#         print("Boards expanded: "+ str(outer_iterations))
        if outer_iterations > max_iterations:
            print('FAILURE: Unable to balance within 10%, returned SIFT balance')
            print_path(min_diff)
            print()
            print("Final manifest preview shown below:\n")
            print_board(min_diff.board)
            return

        if balanced(current_board.board) or reached_partition(current_board.board):
            if sum(current_board.board[rows-1]) == 0:
                print('SUCCESS: SIFT balance operation list found!')
                print("Boards expanded: "+ str(outer_iterations))
                final_board = print_path(current_board)
                print()
                print("Final manifest preview shown below:\n")
                print_board(current_board.board)
                return final_board

        if current_board.f < min_diff.f:
            min_diff = current_board

        for my_container in container_list(current_board.board):
            for possible_move in open_slots(current_board.board, my_container):
                temp_board = [row[:] for row in current_board.board]
                swap(temp_board, my_container, possible_move)
                new_board = Board(temp_board, current_board)

                if len([closed_child for closed_child in closed_list if closed_child == new_board]) > 0:
                    continue

                new_board.g = current_board.g + 1 + manhat(current_board.crane_moveto_pos, my_container) + manhat( my_container, possible_move)
                new_board.h = get_h(new_board.board)
                new_board.f = new_board.g + new_board.h

                new_board.crane_pickup_pos = my_container
                new_board.crane_moveto_pos = possible_move

                if len([open_node for open_node in open_list if new_board == open_node and new_board.g > open_node.g]) > 0:
                    continue
                heapq.heappush(open_list, new_board)

    print('FAILURE: Unable to balance within 10%, returned SIFT balance')
    # print("Boards expanded: "+ str(outer_iterations))
    print_path(min_diff)
    print()
    print("Final manifest preview shown below:\n")
    print_board(min_diff.board)
    return

# Node class to track astar shortest path lengh search states 
class Node():
    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position

        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self,other):
        return self.position == other.position

    def __repr__(self):
        return f"{self.position} - g: {self.g} h: {self.h} f: {self.f}"

    def __lt__(self, other):
        return self.f < other.f

    def __gt__(self, other):
        return self.f > other.f

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

            