# Configuration settings
import os

# Your StarCraft 2 username (only needed if RENAME_FILES is True)
SC2_USERNAME = "YourUsername"  # CHANGE THIS!

# Path to your replays directory
# Update this path to match your system
REPLAYS_PATH = r"C:\Path\To\Your\Replays\Multiplayer"

# Processing settings
REMOVE_CHAT = True      # Remove chat messages from replays
RENAME_FILES = True     # Rename files with WIN/LOSE and opponent race
GENERATE_REPORT = True  # Show statistics after processing
BACKUP_ORIGINALS = True # Create backup before processing (only for renaming)

# What to include in filenames
INCLUDE_DURATION = True     # Add match duration (e.g., "15min")
INCLUDE_MAX_MINERALS = True # Add max unspent minerals (e.g., "2500minerals")

# UI settings
PAUSE_WHEN_DONE = True  # Keep window open after processing (useful for shortcuts)

# Path to MPQEditor 
MPQEDITOR_PATH = r'C:\Path\To\Your\MPQEditor.exe' 