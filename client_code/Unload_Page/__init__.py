from ._anvil_designer import Unload_PageTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from popover import popover

class Unload_Page(Unload_PageTemplate):
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
          button = Button(text=grid_labels[index_row][index_col], background="rgb(173,216,230)"
                               , width="72", font_size=10, bold=True, foreground="rgb(0,0,0)")
        button.set_event_handler('click', self.toggle_offload)   
        button.popover(content=grid_labels[index_row][index_col] + "\n" + str(weights[index_row][index_col]), placement = 'top', trigger='hover')
        gp.add_component(button, row=index_row, col_xs=index_col, width_xs=1
                        , row_spacing=0)
      
    # Add grid component to map
    self.add_component(gp)
    
    # Add button
    confirm_unload_button = Button(text="Confirm", bold=True, background="rgb(0,255,0)", foreground="rgb(255,255,255)")
    confirm_unload_button.set_event_handler('click', self.click_unload)
    cancel_button = Button(text="Cancel", bold=True, background="rgb(255,0,0)", foreground="rgb(255,255,255)")
    cancel_button.set_event_handler('click', self.click_cancel)
    button_row = FlowPanel(align="center", spacing="small")
    button_row.add_component(confirm_unload_button, width=100)
    button_row.add_component(cancel_button, width=100)
    self.add_component(button_row)

  def toggle_offload(self, **event_args):
    # If Yellow
    if event_args['sender'].background == "rgb(255,255,0)":
      event_args['sender'].background = "rgb(173,216,230)"
      # If White
    else:
      event_args['sender'].background="rgb(255,255,0)"
      

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
    open_form('Form1')

