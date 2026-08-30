import gradio as gr
import sys
import gc # CRITICAL: Import the garbage collection module

# --- Consistent Launch Settings and Cache Control ---
DEFAULT_SERVER_NAME = "192.168.0.106"
DEFAULT_SERVER_PORT = 16500
TARGET_URL = f"http://{DEFAULT_SERVER_NAME}:{DEFAULT_SERVER_PORT}"

# delete_cache parameter tuple: (frequency_in_seconds, age_in_seconds)
# This manages disk space by deleting files older than 60s every 60s to prevent disk overflow.
CACHE_CLEANUP_SETTINGS = (60, 60)

# Dictionary mapping selection numbers to (Hugging Face Model ID, Description)
MODEL_CHOICES = {
    # --- Image Generation Models ---
    1: ("stabilityai/stable-diffusion-2-1", "Stable Diffusion 2.1 (General Purpose)"),
    2: ("runwayml/stable-diffusion-v1-5", "Stable Diffusion v1-5 (Classic/Versatile)"),
    3: ("stabilityai/stable-diffusion-xl-refiner-1.0", "SDXL Refiner 1.0 (Detailing/Photorealism)"),
    4: ("prompthero/openjourney", "OpenJourney (Midjourney Style)"),
    5: ("dreamlike-art/dreamlike-photoreal-2.0", "Dreamlike Photoreal 2.0 (High Realism)"),
    6: ("CompVis/stable-diffusion-v1-4", "Stable Diffusion v1-4 (Foundational)"),
    7: ("segmind/tiny-sd", "Tiny-sd (Fast/Efficient)"),
    8: ("lambdalabs/sd-image-variations-diffusers", "Image Variations (Image-to-Image)"),
    9: ("lllyasviel/ControlNet", "ControlNet (Conditional Generation - Complex)"),
    10: ("dall-e-mini/dalle-mini", "DALL-E Mini (Older/Experimental)"),
    11: ("stabilityai/stable-diffusion-xl-base-1.0", "SDXL Base 1.0 (High-Res Text-to-Image)"),
    12: ("cagliostrolab/animagine-xl-3.1", "Animagine XL 3.1 (Anime/Illustration Style)"),
    16: ("stabilityai/stable-diffusion-xl-base-1.0", "SDXL Base 1.0 (Duplicate Entry)"), 
    
    # --- Large Language Models (LLMs) & Code Models ---
    13: ("fka/awesome-chatgpt-prompts", "Awesome ChatGPT Prompts (Prompt Generator/LLM)"),
    14: ("ysharma/CodeGemma", "CodeGemma (Code Generation/LLM)"),
    15: ("google/gemma-7b", "Gemma 7B (General Purpose LLM)"),
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
            
# --- AGGRESSIVE MEMORY CLEANUP HOOK (The Core Fix) ---
def memory_reset():
    """Forces the Python garbage collector to free up memory and prints status."""
    gc.collect()
    print("\n[INFO]: Aggressive GC performed after interaction to stabilize memory.")
    # Must return an empty list to satisfy Gradio's event handler signature for outputs=None
    return [] 

if __name__ == "__main__":
    # Get the selected model ID and description
    selected_model_id, selected_desc = get_user_choice()
    
    print(f"\n🚀 Launching Gradio with: **{selected_desc}**...")
    print(f"Model ID: {selected_model_id}")
    print(f"Target URL: {TARGET_URL}")
    print(f"Memory Management: Max threads set to 1. GC hook attached to prediction button.")
    print("-------------------------------------------------------")

    try:
        # 🔑 CRITICAL FIX: Use gr.load() and explicitly set src="huggingface"
        remote_interface = gr.load(selected_model_id, src="huggingface") 
        
        # --- ATTACHING THE GC HOOK (Component Search) ---
        found_submit_button = False
        
        # Iterate over all children/components to find a usable Button
        # This is resilient against different Space layouts.
        for component in remote_interface.get_children():
            if isinstance(component, gr.Button):
                if component.label and component.label.lower() in ["submit", "run", "generate"]:
                    # Attach the memory_reset function as a side-effect after the model runs.
                    component.click(
                        memory_reset, 
                        inputs=[], 
                        outputs=[], 
                        queue=False # Ensure it runs immediately without queuing
                    )
                    print(f"[SUCCESS]: Attached memory reset hook to the '{component.label}' button.")
                    found_submit_button = True
                    break # Stop after finding the first submission button
        
        if not found_submit_button:
            print("[WARNING]: Could not find a suitable button component to attach the GC hook. GC hook not attached.")

        # Launch the loaded interface with minimal threads for memory economy
        remote_interface.launch(
            server_name=DEFAULT_SERVER_NAME, 
            server_port=DEFAULT_SERVER_PORT, 
            show_api=True,
            delete_cache=CACHE_CLEANUP_SETTINGS,
            # CRITICAL: Restrict concurrent server threads to MINIMUM.
            max_threads=1 
        )
        
    except Exception as e:
        print(f"\n❌ An error occurred during Gradio launch: {e}")
        input("Press Enter to exit...")
        sys.exit(1)