import zipfile
import os
import shutil

def create_apworld(folder_path: str, output_name: str = None):
    if not os.path.isdir(folder_path):
        print("Invalid folder path.")
        return

    # Default name based on folder if not specified
    if output_name is None:
        output_name = os.path.basename(folder_path)

    zip_path = f"{output_name}.zip"
    apworld_path = f"{output_name}.apworld"

    # Remove existing .apworld if it exists
    if os.path.exists(apworld_path):
        os.remove(apworld_path)

    # Create zip file
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, folder_path)
                zipf.write(full_path, rel_path)

    # Rename to .apworld
    shutil.move(zip_path, apworld_path)
    print(f"Packed and renamed to: {apworld_path}")

# Example usage:
create_apworld(r"C:\Users\micha.DESKTOP-Q740MKF\Documents\GitHub\FTLMultiverseArchipelago\manual_ftlmultiverse_version04")
