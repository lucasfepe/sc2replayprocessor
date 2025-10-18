import os
from pathlib import Path
import re

# Path to your replays directory
REPLAYS_PATH = r"C:\Users\lucas\OneDrive\Documents\StarCraft II\Accounts\92300375\1-S2-1-4740127\Replays\Multiplayer"

replay_dir = Path(REPLAYS_PATH)
renamed_count = 0

# Pattern to match the redundant format: date_result_race_duration_minerals_date_result_race_originalname
pattern = re.compile(r'^(\d{4}-\d{2}-\d{2})_([^_]+)_vs_([^_]+)_(\d+min)_(\d+minerals)_\d{4}-\d{2}-\d{2}_[^_]+_vs_[^_]+_(.+)$')

for file_path in replay_dir.glob("*"):
    if file_path.is_file() and (file_path.suffix == ".SC2Replay" or file_path.suffix == ".processed"):
        old_name = file_path.name
        match = pattern.match(file_path.stem)
        
        if match:
            # Extract the parts we want to keep
            date = match.group(1)
            result = match.group(2)
            race = match.group(3)
            duration = match.group(4)
            minerals = match.group(5)
            original_name = match.group(6)
            
            # Create new name without date (as requested)
            # Format: WIN_vs_Race_Duration_Minerals_OriginalName
            new_stem = f"{result}_vs_{race}_{duration}_{minerals}_{original_name}"
            new_name = new_stem + file_path.suffix
            new_path = file_path.parent / new_name
            
            try:
                file_path.rename(new_path)
                print(f"✅ Fixed: {old_name}")
                print(f"   → {new_name}")
                renamed_count += 1
            except FileExistsError:
                print(f"⚠️  File already exists: {new_name}")
            except Exception as e:
                print(f"❌ Error renaming {old_name}: {e}")

print(f"\n🎉 Fixed {renamed_count} files!")
input("\nPress Enter to exit...")