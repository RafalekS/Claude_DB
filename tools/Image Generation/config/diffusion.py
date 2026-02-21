import gradio as gr
gr.load("models/runwayml/stable-diffusion-v1-5").launch(server_name="192.168.0.106", server_port="15655", show_api=True)