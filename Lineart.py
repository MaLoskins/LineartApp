import os
import sys

# For environment: C:\AI\stable-diffusion-webui-forge\venv\Scripts\activate.bat
# OR GIT Bash:
# source C:/AI/stable-diffusion-webui-forge/venv/Scripts/activate

# To Create Comfy Script (Comfy must be running): python -m comfy_script.transpile <workflow>.json

# Import ComfyScript modules
sys.path.append(r'C:\AI\ComfyUI\custom_nodes\ComfyScript\src')
from comfy_script.runtime import *
load()  # Load ComfyUI
from comfy_script.runtime.nodes import *

def call_lineart(output_dir, positive_prompt, image_path, seed=134176473189985):
    try:
        print(f"call_lineart called with output_dir: {output_dir}, prompt: '{positive_prompt}', image_path: {image_path}")
        with Workflow():
            # Load models
            model, clip, vae = CheckpointLoaderSimple('dreamshaper_8.safetensors')
            positive_condition = CLIPTextEncode(positive_prompt, clip)
            negative_condition = CLIPTextEncode('uncensored', clip)
            
            # Load ControlNet
            control_net = ControlNetLoader('controlnet11Models_lineart.safetensors')
            
            # Load image
            image, _ = LoadImage(image_path)
            
            # Apply ControlNet
            positive, negative = ControlNetApplyAdvanced(
                positive_condition,
                negative_condition,
                control_net,
                image,
                1, 0, 1,
                vae
            )
            
            # Generate latent image
            latent = EmptyLatentImage(720, 720, 1)
            latent = KSampler(
                model, seed, 20, 6,
                'dpmpp_2s_ancestral', 'karras',
                positive, negative,
                latent, 1
            )
            
            # Decode image
            image2 = VAEDecode(latent, vae)
            
            # Save image
            edited_image_path = os.path.join(output_dir, "image.png")
            JWImageSaveToPath(edited_image_path, image2, 'true')
            print(f"Edited image saved at {edited_image_path}")
        
    except Exception as e:
        print(f"An error occurred in call_lineart: {e}")
