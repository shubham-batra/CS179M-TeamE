from ._anvil_designer import Balance_SlideTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from popover import popover

step_number = 1

def display_step(self, step):
  button_list = self.get_components()[0].get_components()
  for row in range(8):
    for col in range(12):
      button = button_list[row*12+col]
      if col == step[0][1] and 7-row >= min(step[0][0], step[1][0]) and 7-row <= max(step[0][0], step[1][0]):
        button.background = "rgb(255, 255, 0)"
      if 7-row == step[1][0] and col >= min(step[0][1], step[1][1]) and col <= max(step[0][1], step[1][1]):
        button.background = "rgb(255, 255, 0)"
      if 7-row == step[0][0] and col == step[0][1]:
        button.background = "rgb(255,0,0)"
      if 7-row == step[1][0] and col == step[1][1]:
        button.background = "rgb(0,255,0)"

def refresh_grid_color(self):
  button_list = self.get_components()[0].get_components()
  for row in range(8):
    for col in range(12):
      button = button_list[row*12+col]
      if not button.background =="rgb(0,0,0)" and button.text == "":
        button.background = ""
      if not button.background =="rgb(0,0,0)" and not button.text == "":
        button.background = "rgb(173,216,230)"
        
def swap(self, step):
  button_list = self.get_components()[0].get_components()
  button_start = Button()
  button_end = Button()
  for row in range(8):
    for col in range(12):
      button = button_list[row*12+col]
      if 7-row == step[0][0] and col == step[0][1]:
        button_start = button
      if 7-row == step[1][0] and col == step[1][1]:
        button_end = button
        
  button_temp = button_start
  button_start = button_end
  button_end = button_temp
  
  refresh_grid_color(self)  

def jump_to_step(self, step_number):
    for step_index in range(step_number-1):
      step = anvil.server.call('get_balance_step', step_index+1)
      if (len(step)) == 0:
        break;
      print("hello")
      swap(self, step)
    
    step = anvil.server.call('get_balance_step',step_number)
    display_step(self, step)     
    refresh_grid_color(self)
        
class Balance_Slide(Balance_SlideTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run when the form opens.
    
    # Dynamically generating the ship grid
    grid_labels, weights = anvil.server.call('load_manifest_grid')

    # Default way container looks
#      chars = ["0", "0", '0', '0', '0','0','0','0','0','0','0','0',
#              "0", '0', '0', '0', '0','0','0','0','0','0','0','0',
#              "0", '0', '0', '0', '0','0','0','0','0','0','0','0',
#              "0", '0', '0', '0', '0','0','0','0','0','0','0','0',
#              "0", '0', '0', '0', '0','0','0','0','0','0','0','0',
#              "0", '0', '0', '0', '0','0','0','0','0','0','0','0',
#              "0", '0', '0', '0', '0','0','0','0','0','0','0','0',
#              "0", '0', '0', '0', '0','0','0','0','0','0','0','0']
    
    # Make GridPanel
    gp = GridPanel()
    
    # Reverse grid labels
    grid_labels.reverse()
    weights.reverse()
    
    # row number
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
        button.popover(content=grid_labels[index_row][index_col] + "\n" + str(weights[index_row][index_col]), placement = 'top', trigger='hover')
        gp.add_component(button, row=index_row, col_xs=index_col, width_xs=1
                        , row_spacing=0)
      
    # Add grid component to map
    self.add_component(gp)
    
    # Add button
    confirm_unload_button = Button(text="Next", bold=True, background="rgb(180,180,180)", foreground="rgb(255,255,255)")
    confirm_unload_button.set_event_handler('click', self.click_unload)
    cancel_button = Button(text="Cancel", bold=True, background="rgb(255,0,0)", foreground="rgb(255,255,255)")
    cancel_button.set_event_handler('click', self.click_cancel)
    button_row = FlowPanel(align="center", spacing="small")
    button_row.add_component(confirm_unload_button, width=100)
    button_row.add_component(cancel_button, width=100)
    self.add_component(button_row)
    
    jump_to_step(self, 2)
    
      
  def click_unload(self, **event_args):
    unload_containers = []
    button_list = self.get_components()[1].get_components()
    for row in range(8):
      for col in range(12):
        button = button_list[row*12+col]
        if button.background == "rgb(255,255,0)":
          unload_containers.append((7-row, col, button.text))
      
    anvil.server.call('write_unload_containers', unload_containers)
    open_form('Input_Load')
  
  
  def click_cancel(self, **event_args):
    open_form('Home')
