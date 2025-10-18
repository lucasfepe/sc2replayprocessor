# StarCraft 2 Replay Renamer

This tool renames SC2 replay files to include match date, win/loss status, and opponent race.

## Setup

1. Install Python 3.7+  
2. Clone this repository  
3. Install dependencies:
   
    (use an indented code block so this markdown can be pasted safely)
    
    ```
    pip install -r requirements.txt
    ```
4. Update `config.py` with:
   - your SC2 username  
   - the path to your replays folder

## Usage

Run the script from the project root:
```
python rename_replays.py
```

## Output Format

Files are renamed to:  
`YYYY-MM-DD_WIN/LOSE_vs_RACE_originalname.SC2Replay`

**Example:**  
`2024-01-15_WIN_vs_Terran_King's Cove LE.SC2Replay`

## Features

- Automatically extracts win/loss from replay files  
- Identifies opponent race  
- Creates backups before renaming  
- Generates match statistics report  
- Handles `.processed` marker files
