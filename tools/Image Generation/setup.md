xx`
c:\Users\r_sta\.lmstudio\models\sd-1\

https://github.com/akoww/InvokeAI-DirectML?tab=readme-ov-file
https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Install-and-Run-on-AMD-GPUs





1. Automatic1111's Stable Diffusion WebUI

Official GitHub Repository: https://github.com/AUTOMATIC1111/stable-diffusion-webui
Why It's a Good Alternative: This is one of the most popular and feature-rich web UIs for Stable Diffusion, with built-in DirectML support for AMD GPUs on Windows. It can utilize your Radeon 780M's ~12GB shared VRAM for faster generations (e.g., 30-60 seconds per 512x512 image) compared to pure CPU mode in InvokeAI. It supports the same models, LoRAs, and prompts as InvokeAI.
Quick Setup for Your Hardware:

Clone the repo: Open Command Prompt and run git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git.
Navigate to the folder: cd stable-diffusion-webui.
Download the Stable Diffusion 1.5 model (e.g., v1-5-pruned-emaonly.safetensors from https://huggingface.co/runwayml/stable-diffusion-v1-5) and place it in models/Stable-diffusion/.
Run with DirectML: webui-user.bat (it auto-installs dependencies). To enable AMD GPU, edit webui-user.bat and add --use-directml to the COMMANDLINE_ARGS line (e.g., set COMMANDLINE_ARGS=--use-directml --precision full --no-half for stability on iGPUs).
Launch the web UI at http://127.0.0.1:7860. Start with low-res prompts (512x512, 20 steps) and monitor VRAM usage.


Documentation: Check the repo's wiki for AMD-specific tips: https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki.
Potential Issues: Ensure your AMD Adrenalin drivers are updated. If VRAM overflows, add --medvram to the args.



2. ComfyUI

Official GitHub Repository: https://github.com/comfyanonymous/ComfyUI
Why It's a Good Alternative: ComfyUI is a node-based, modular GUI that's highly efficient and extensible for diffusion models. It has experimental DirectML support for AMD on Windows (via PyTorch's DirectML backend), making it suitable for your 780M iGPU. It's lighter than Automatic1111 and great for custom workflows, with similar performance to InvokeAI but more flexibility.
Quick Setup for Your Hardware:

Clone the repo: git clone https://github.com/comfyanonymous/ComfyUI.git.
Navigate: cd ComfyUI.
Install dependencies: Run pip install torch-directml (for AMD support) followed by pip install -r requirements.txt.
Download the SD 1.5 model to models/checkpoints/ (same Hugging Face link as above).
Launch with DirectML: python main.py --directml (this enables the backend). The UI opens at http://127.0.0.1:8188.
Load a basic workflow (e.g., from examples in the repo) and use nodes for text-to-image. Limit to 512x512 for your VRAM.


Documentation: Full installation guide at https://github.com/comfyanonymous/ComfyUI/blob/master/README.md; examples at https://comfyanonymous.github.io/ComfyUI_examples/.
Potential Issues: DirectML is "badly supported" on Windows per the docs, so test with --cpu fallback if needed. For better AMD integration, community nodes like ComfyUI-Manager can help: https://github.com/Comfy-Org/ComfyUI-Manager.



3. InvokeAI-DirectML Fork (Unofficial for Windows AMD Support)

GitHub Repository: https://github.com/akoww/InvokeAI-DirectML
Why It's a Good Alternative: This is a community-maintained fork of InvokeAI that adds DirectML support specifically for AMD GPUs on Windows (including iGPUs like your 780M). It retains the familiar InvokeAI interface and WebUI while enabling GPU acceleration, which the official version lacks on Windows.
Quick Setup for Your Hardware:

Clone the fork: git clone https://github.com/akoww/InvokeAI-DirectML.git.
Follow the repo's installation: Run the installer script or manual setup (it creates a virtual environment).
Download the SD 1.5 model to the models folder as before.
Configure for DirectML: Edit the config to use device: cuda (it maps to DirectML internally for AMD), and run with --directml flag if prompted.
Launch: invoke.bat --directml (or similar, per README). Access the UI at localhost:9090.


Documentation: Detailed README at https://github.com/akoww/InvokeAI-DirectML/blob/main/README.md. It notes support for Windows AMD via DirectML.
Potential Issues: As a fork, it may lag behind official updates—check for compatibility with your InvokeAI version. Test VRAM limits as before.



General Tips for All Alternatives

Model Compatibility: All support the Stable Diffusion 1.5 checkpoint from https://huggingface.co/runwayml/stable-diffusion-v1-5. Download the safetensors file and place it in the appropriate models folder.
AMD Drivers: Update to the latest Adrenalin edition via AMD's site for best DirectML performance.
VRAM Management: With your 11.97GB VRAM capacity, stick to fp16 precision and resolutions under 768x768. Use tools like MSI Afterburner to monitor GPU usage.
If Issues Persist: Fall back to CPU mode in these tools, or consider a Linux VM (e.g., via VirtualBox) for official InvokeAI with ROCm—AMD's ROCm docs: https://rocm.docs.amd.com/.

If you need step-by-step installation commands, troubleshooting for a specific tool, or links to more resources (e.g., Reddit guides), just let me know—I'm here to help make this work smoothly!