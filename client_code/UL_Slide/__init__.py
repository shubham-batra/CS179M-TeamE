from ._anvil_designer import UL_SlideTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

import copy

step_number = 1
load_number = 0

def load_page(self):
  self.clear()
  # Dynamically generating the ship grid
  grid_labels, weights = anvil.server.call('load_manifest_grid')

  # Make Instruction Label
  instruction = Label(text="INSTRUCTIONS", align="center", bold=True, font_size=20)
  self.add_component(instruction)
  
  # Make GridPanel
  gp = GridPanel()
  
  # Reverse grid labels
  grid_labels.reverse()
  weights.reverse()
  
  # Make extra buffer rows
  for index_row in range(2):
    for index_col in range(12):
      button = Button(text="", enabled=False, width="72", font_size=10, bold=True)
      button.tooltip = "UNUSED\n0"
      gp.add_component(button, row=index_row, col_xs=index_col, width_xs=1
                        , row_spacing=0)
  
  # Add manifest data
  for index_row in range(len(grid_labels)):
    for index_col in range(len(grid_labels[index_row])):
      button = Button()
      if "UNUSED" in grid_labels[index_row][index_col]:
        button = Button(text="", enabled=False, width="72", font_size=10, bold=True)

      elif "NAN" in grid_labels[index_row][index_col]:
        button = Button(text="", background="rgb(0,0,0)", enabled=False, width="72", font_size=10, bold=True)

      else:
        button = Button(text=grid_labels[index_row][index_col], background="rgb(173,216,230)", enabled=True
                              , width="72", font_size=10, bold=True, foreground="rgb(0,0,0)")
      button.tooltip = grid_labels[index_row][index_col] + "\n" + str(weights[index_row][index_col])
      gp.add_component(button, row=index_row+2, col_xs=index_col, width_xs=1
                      , row_spacing=0)
    
  # Add grid component to map
  self.add_component(gp)
  
  # Add button
  next_button = Button(text="Next", bold=True, background="rgb(180,180,180)", foreground="rgb(255,255,255)")
  next_button.set_event_handler('click', self.click_next)
  cancel_button = Button(text="Cancel", bold=True, background="rgb(255,0,0)", foreground="rgb(255,255,255)")
  cancel_button.set_event_handler('click', self.click_cancel)
  button_row = FlowPanel(align="center", spacing="small")
  button_row.add_component(next_button, width=100)
  button_row.add_component(cancel_button, width=100)
  self.add_component(button_row)
  
  # Add label for estimated time
  est_time = anvil.server.call('get_est_time')
  time_text = 'Total Estimated Time: ' + est_time + ' minutes'
  est_time_label = Label(text=time_text, align='center',spacing_above='10')
  self.add_component(est_time_label)

def display_step(self, step):
  button_list = self.get_components()[1].get_components()
  for row in range(10):
    for col in range(12):
      button = button_list[row*12+col]
      
      if step[0][0] <= step[1][0]:
        if col == step[0][1] and 9-row >= min(step[0][0], step[1][0]) and 9-row <= max(step[0][0], step[1][0]):
          button.background = "rgb(255, 255, 0)"
        if 9-row == step[1][0] and col >= min(step[0][1], step[1][1]) and col <= max(step[0][1], step[1][1]):
          button.background = "rgb(255, 255, 0)"
      else:
        if col == step[1][1] and 9-row >= min(step[1][0], step[0][0]) and 9-row <= max(step[1][0], step[0][0]):
          button.background = "rgb(255, 255, 0)"
        if 9-row == step[0][0] and col >= min(step[1][1], step[0][1]) and col <= max(step[1][1], step[0][1]):
          button.background = "rgb(255, 255, 0)"
      if 9-row == step[0][0] and col == step[0][1]:
        if step[3] == "L":
          button.background = "rgb(251,72,196)"
        else:
          button.background = "rgb(255,0,0)"
      if 9-row == step[1][0] and col == step[1][1]:
        if step[3] == "U":
          button.background = "rgb(251,72,196)"
        else:
          button.background = "rgb(0,255,0)"

def refresh_grid_color(self):
  button_list = self.get_components()[1].get_components()
  for row in range(10):
    for col in range(12):
      button = button_list[row*12+col]
      if "NAN" in button.tooltip:
        button.background = "rgb(0,0,0)"
        button.enabled = False
      elif "UNUSED" in button.tooltip:
        button.background = ""
        button.enabled = False
      elif not button.tooltip == "":
        button.background = "rgb(173,216,230)"
        button.foreground = "rgb(0,0,0)"
        button.enabled = True
        
def swap(self, step, weight=-1):
  button_list = self.get_components()[1].get_components()
  
  if step[3] == "M":
    button_start = Button()
    button_end = Button()
    for row in range(10):
      for col in range(12):
        button = button_list[row*12+col]
        if 9-row == step[0][0] and col == step[0][1]:
          button_start = button
        if 9-row == step[1][0] and col == step[1][1]:
          button_end = button
          
    button_temp_text = button_start.text
    button_temp_tooltip = button_start.tooltip
    button_start.text = button_end.text
    button_start.tooltip = button_end.tooltip
    button_end.text = button_temp_text
    button_end.tooltip = button_temp_tooltip
  if step[3] == "U":
    button_start = Button()
    for row in range(10):
      for col in range(12):
        button = button_list[row*12+col]
        if 9-row == step[0][0] and col == step[0][1]:
          button_start = button
    button_start.text = ""
    button_start.tooltip = "UNUSED\n0"
    
  if step[3] == "L":
    button_end = Button()
    for row in range(10):
      for col in range(12):
        button = button_list[row*12+col]
        if 9-row == step[1][0] and col == step[1][1]:
          button_end = button
    button_end.text = step[2]
    button_end.tooltip = step[2] + "\n" + str(weight)
  
  refresh_grid_color(self)
  
  
def input_weight(self, step, load_number):

  self.clear()
  
  # Ask for weight

  instruction_weight = Label(text="Move the crane to load container " + step[2][:7] + "\nWeigh the container on the scale and input the weight", align="center", bold=True, font_size=20)
  instruction_weight.tooltip = load_number
  textbox_weight = TextBox(placeholder="Type here", type="number")
  submit_button = Button(text="Submit Weight", bold=True, background="rgb(0,255,0)", foreground="rgb(255,255,255)")
  submit_button.set_event_handler('click', self.click_submit_weight)
  
  self.add_component(instruction_weight)
  self.add_component(textbox_weight)
  self.add_component(submit_button)

def jump_to_step(self, step_number, after_input_weight=False):
    
    # reset stats
    load_page(self)
    global load_number
    load_number = 0
  
    for step_index in range(step_number-1):
      step = anvil.server.call('get_operation_step', step_index+1)
      # No more steps
      if (len(step)) == 0:
        self.get_components()[2].get_components()[0].text = "Finish"
        self.get_components()[2].get_components()[0].background = "rgb(0,255,0)"
        self.get_components()[0].text = "Confirm ship state"
        return
      
      weight = -1
      if step[3] == "L":
        load_list = anvil.server.call('load_load_textfile')
        if load_list[load_number][1] == "":
          weight = 99999
        else:
          weight = load_list[load_number][1]
        load_number = load_number + 1
      swap(self, step, weight)
    
    step = anvil.server.call('get_operation_step',step_number)
    if (len(step)) == 0:
      self.get_components()[2].get_components()[0].text = "Finish"
      self.get_components()[2].get_components()[0].background = "rgb(0,255,0)"
      self.get_components()[0].text = "Confirm ship state"
      return
    
    if step[3] == "M":
      self.get_components()[0].text = "Move container " + step[2][:7] + " from the red to the green along the yellow path"
    if step[3] == "L" and not after_input_weight:
      input_weight(self, step, load_number)
      return
    if step[3] == "L" and after_input_weight:
      self.get_components()[0].text = "Load container " + step[2][:7] + " from the pink to the green along the yellow path"
    if step[3] == "U":
      self.get_components()[0].text = "Unload container " + step[2][:7] + " from the red to the pink along the yellow path"
      
    display_step(self, step) 
    
def next_step(self):
  
  global step_number
  step_number = step_number + 1
  global load_number
  
  if step_number >= 2:
    step = anvil.server.call('get_operation_step', step_number-1)
    weight = -1
    if step[3] == "L":
      load_list = anvil.server.call('load_load_textfile')
      if load_list[load_number][1] == "":
        weight = 99999
      else:
        weight = load_list[load_number][1]
      load_number = load_number + 1
    if step[3] == "M":
      anvil.server.call('write_log',"Moved " + step[2] + " from (" + str(step[0][0]) + "," + str(step[0][1]) + ") to (" + str(step[1][0]) + "," + str(step[1][1]) + ")")
    if step[3] == "L":
      anvil.server.call('write_log',"Loaded " + step[2] + " to (" + str(step[1][0]) + "," + str(step[1][1]) + ")")
    if step[3] == "U":
      anvil.server.call('write_log',"Unloaded " + step[2] + " from (" + str(step[0][0]) + "," + str(step[0][1]) + ")")
    swap(self, step, weight)
  step = anvil.server.call('get_operation_step',step_number)
  if (len(step)) == 0:
    self.get_components()[2].get_components()[0].text = "Finish"
    self.get_components()[2].get_components()[0].background = "rgb(0,255,0)"
    self.get_components()[0].text = "Confirm ship state"
    return
  
  if step[3] == "M":
    self.get_components()[0].text = "Move container " + step[2][:7] + " from the red to the green along the yellow path"
  if step[3] == "L":
    input_weight(self, step, load_number)
    return
  if step[3] == "U":
    self.get_components()[0].text = "Unload container " + step[2][:7] + " from the red to the pink along the yellow path"
    
  display_step(self, step)     
  
        
class UL_Slide(UL_SlideTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run when the form opens.
    
    load_page(self)
    
    global load_number
    load_number = 0
    
    global step_number
    # Checking for backup and setting step number as necessary
    backup_pressed = anvil.server.call('get_backup_pressed')
    if backup_pressed == 1:
      step_number = int(anvil.server.call('load_backup')[1])
      jump_to_step(self,step_number, True)
    else:
      step_number = 0
      next_step(self)
    
    
    
    
    
      
  def click_submit_weight(self, **event_args):
    
    # save into load_list.txt the new weight
    if self.get_components()[1].text is None:
      self.get_components()[1].placeholder = "Cannot be empty!"
      return
    container_index = int(self.get_components()[0].tooltip)
    weight = self.get_components()[1].text
    anvil.server.call('write_load_container_weight', container_index, weight)
    
    global step_number
    jump_to_step(self, step_number, True)
      
  def click_next(self, **event_args):
    if self.get_components()[2].get_components()[0].text == "Finish":
      anvil.server.call('write_log',"Finished unloading/loading " + anvil.server.call('load_input_manifest_path'))
      anvil.server.call('compile_UL_manifest')
      anvil.server.call('set_backup_pressed',0)
      open_form('Home')
      return
    next_step(self)
  
  def click_cancel(self, **event_args):
    anvil.server.call('set_backup_pressed',0)
    open_form('Home')
