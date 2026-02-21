# Step 1: Execute the Python script using your specific Python executable
# The Python script will pause until the user selects a model, then it launches Gradio.
& "C:\Program Files\Python\python.exe" ".\models.py"

# Step 2: Open Brave browser with the correct IP and port
# This command is executed immediately after the Python script starts,
# so the browser is ready when Gradio finishes loading the model.
start brave.exe "http://192.168.0.106:16500"