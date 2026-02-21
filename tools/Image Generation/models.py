import gradio as gr
import sys

# Define the consistent launch settings
DEFAULT_SERVER_NAME = "192.168.0.106"
DEFAULT_SERVER_PORT = 16500
TARGET_URL = f"http://{DEFAULT_SERVER_NAME}:{DEFAULT_SERVER_PORT}"


# Dictionary mapping selection numbers to (Hugging Face Model ID, Description)
MODEL_CHOICES = {
    # --- Original 10 Models (All are image generation models) ---
    1: ("stabilityai/stable-diffusion-2-1", "Stable Diffusion 2.1 (General Purpose)"),
    2: ("runwayml/stable-diffusion-v1-5", "Stable Diffusion v1-5 (Classic/Versatile)"),
    3: ("stabilityai/stable-diffusion-xl-refiner-1.0", "SDXL Refiner 1.0 (Detailing/Photorealism)"),
    4: ("prompthero/openjourney", "OpenJourney (Midjourney Style)"),
    5: ("dreamlike-art/dreamlike-photoreal-2.0", "Dreamlike Photoreal 2.0 (High Realism)"),
    6: ("CompVis/stable-diffusion-v1-4", "Stable Diffusion v1-4 (Foundational)"),
    7: ("segmind/tiny-sd", "Tiny-SD (Fast/Efficient)"),
    8: ("lambdalabs/sd-image-variations-diffusers", "Image Variations (Image-to-Image)"),
    9: ("lllyasviel/ControlNet", "ControlNet (Conditional Generation - Complex)"),
    10: ("dall-e-mini/dalle-mini", "DALL-E Mini (Older/Experimental)"),
    
    # --- New 8 Models (Includes image generation and LLMs) ---
    11: ("stabilityai/stable-diffusion-xl-base-1.0", "SDXL Base 1.0 (High-Res Text-to-Image)"),
    12: ("cagliostrolab/animagine-xl-3.1", "Animagine XL 3.1 (Anime/Illustration Style)"),
    13: ("fka/awesome-chatgpt-prompts", "Awesome ChatGPT Prompts (Prompt Generator/LLM)"),
    14: ("ysharma/CodeGemma", "CodeGemma (Code Generation/LLM)"),
    15: ("google/gemma-7b", "Gemma 7B (General Purpose LLM)"),
    16: ("stabilityai/stable-diffusion-xl-base-1.0", "SDXL Base 1.0 (Duplicate of 11)"),
    17: ("WizardLM/WizardCoder-15B-V1.0", "WizardCoder 15B (Code Generation/LLM)"),
    18: ("Xwin-LM/XwinCoder-34B", "XwinCoder 34B (Code Generation/LLM)"),
}

def display_menu():
    """Prints the model selection menu."""
    print("\n" + "="*80)
    print("                      🖼️  Gradio Model Selector 🤖")
    print("="*80)
    print(f"{'#':<3} | {'Model ID':<40} | {'Description':<30} | {'Launch URL'}")
    print("-" * 80)
    for num, (model_id, desc) in MODEL_CHOICES.items():
        print(f"[{num:2}]: {model_id:<40} | {desc:<30} | {TARGET_URL}")
    print("="*80)

def get_user_choice():
    """Prompts the user for a choice and validates the input."""
    while True:
        display_menu()
        try:
            choice = int(input(f"Enter the number of the model you want to run (1-{len(MODEL_CHOICES)}): "))
            if choice in MODEL_CHOICES:
                return MODEL_CHOICES[choice]
            else:
                print(f"⚠️ Invalid choice. Please enter a number between 1 and {len(MODEL_CHOICES)}.")
        except ValueError:
            print("⚠️ Invalid input. Please enter a number.")

if __name__ == "__main__":
    # Get the selected model ID and description
    selected_model_id, selected_desc = get_user_choice()
    
    print(f"\n🚀 Launching Gradio with: **{selected_desc}**...")
    print(f"Model ID: {selected_model_id}")
    print(f"Target URL: {TARGET_URL}")
    print("-------------------------------------------------------")

    try:
        # Load and launch the selected model using the consistent launch settings
        gr.load(f"models/{selected_model_id}").launch(
            server_name=DEFAULT_SERVER_NAME, 
            server_port=DEFAULT_SERVER_PORT, 
            show_api=True
        )
    except Exception as e:
        print(f"\n❌ An error occurred during Gradio launch: {e}")
        input("Press Enter to exit...")
        sys.exit(1)