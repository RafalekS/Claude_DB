import os
import customtkinter

json_file_path = "./themes/Sweetkind.json"
customtkinter.set_default_color_theme(json_file_path)
customtkinter.set_appearance_mode("dark")  # Modes: system (default), light, dark
from customtkinter import CTk, CTkButton, CTkEntry, CTkLabel, CTkToplevel

class GradioServerConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gradio Server Config")
        self.root.geometry("500x400")
        root.resizable(True, True)
        
        # Labels and text input windows with spacing
        labels = ["File Name:", "AI Model:", "Server IP:", "Port Number:"]
        self.entries = []
        y_coord = 25
        for label_text in labels:
            label = CTkLabel(self.root, text=label_text)
            label.place(x=20, y=y_coord)
            entry = CTkEntry(self.root, width=250)
            entry.place(x=150, y=y_coord)
            self.entries.append(entry)
            y_coord += 40  # Adjusted spacing between widgets

        # Generate Config button
        self.generate_button = CTkButton(self.root, text="Generate Config", command=self.generate_and_save_config)
        self.generate_button.place(x=20, y=200)

        # Config display
        self.config_display = CTkLabel(self.root, text="Config", wraplength=300, width=200, height=200, anchor="w")
        self.config_display.place(x=20, y=240)

    def generate_and_save_config(self):
        model_name = self.entries[0].get()
        ai_model = self.entries[1].get()
        server_ip = self.entries[2].get()
        port_number = self.entries[3].get()

        config_text = f"import gradio as gr\ngr.load(\"models/{ai_model}\").launch(server_name=\"{server_ip}\", server_port=\"{port_number}\", show_api=True)"
        self.config_display.configure(text=config_text)

        # Save config file to the "config" subfolder
        config_folder = "config"
        if not os.path.exists(config_folder):
            os.makedirs(config_folder)
        file_name = os.path.join(config_folder, f"{model_name}.py")
        with open(file_name, 'w') as file:
            file.write(config_text)
        print(f"Config file '{file_name}' saved successfully.")

if __name__ == "__main__":
    root = CTk()
    app = GradioServerConfigApp(root)
    root.mainloop()
