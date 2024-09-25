import ipywidgets as widgets
from IPython.display import display

VIDEO_URIS = []

videos_textarea = widgets.Textarea(
  value='',
  placeholder='Enter list of video URIs here (one per line or use commas)...',
  description='Videos:',
  layout=widgets.Layout(width='50%', height='200px')
)

# Create a button widget
videos_button = widgets.Button(
  description='Load Video URIs',
  button_style='success'
)

def videos_load(button):
  global VIDEO_URIS
  VIDEO_URIS = [uri.strip() for uri in videos_textarea.value.replace(',', '\n').split('\n')]

videos_button.on_click(videos_load)
display(textarea1, button)
