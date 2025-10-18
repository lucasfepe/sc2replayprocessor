import os
import sys
from datetime import datetime
from sc2reader import load_replay
import shutil
from pathlib import Path
import config

class SC2ReplayRenamer:
    def __init__(self, player_name, replay_dir):
        self.player_name = player_name
        self.replay_dir = Path(replay_dir)
        self.stats = {
            'processed': 0,
            'skipped': 0,
            'errors': 0,
            'wins': 0,
            'losses': 0,
            'vs_Terran': 0,
            'vs_Protoss': 0,
            'vs_Zerg': 0
        }
        
    def backup_replay(self, replay_path):
        """Create backup of original replay"""
        backup_dir = self.replay_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        backup_path = backup_dir / os.path.basename(replay_path)
        shutil.copy2(replay_path, backup_path)
        return backup_path
        
    def get_replay_info(self, replay_path):
        """Extract win/loss and opponent race from replay"""
        try:
            replay = load_replay(str(replay_path))
            
            player_result = None
            opponent_race = None
            
            # Handle 1v1 games
            if len(replay.players) == 2:
                for player in replay.players:
                    if self.player_name.lower() in player.name.lower():
                        player_result = "WIN" if player.result == "Win" else "LOSE"
                    else:
                        opponent_race = player.play_race
                        
            return player_result, opponent_race
            
        except Exception as e:
            print(f"❌ Error reading {replay_path.name}: {e}")
            return None, None
            
    def should_skip_file(self, filename):
        """Check if file should be skipped"""
        skip_patterns = ["_WIN_vs_", "_LOSE_vs_"]
        return any(pattern in filename for pattern in skip_patterns)
        
    def rename_replay(self, replay_path):
        """Rename a single replay file"""
        filename = replay_path.name
        
        # Skip if already renamed
        if self.should_skip_file(filename):
            print(f"⏭️  Skipping already renamed: {filename}")
            self.stats['skipped'] += 1
            return
            
        # Get file date
        file_date = datetime.fromtimestamp(replay_path.stat().st_mtime).strftime('%Y-%m-%d')
        
        # Get replay info
        result, opponent_race = self.get_replay_info(replay_path)
        
        if not result or not opponent_race:
            print(f"❌ Could not extract info from: {filename}")
            self.stats['errors'] += 1
            return
            
        # Update statistics
        if result == "WIN":
            self.stats['wins'] += 1
        else:
            self.stats['losses'] += 1
        self.stats[f'vs_{opponent_race}'] += 1
        
        # Create new filename
        base_name = replay_path.stem
        new_name = f"{file_date}_{result}_vs_{opponent_race}_{base_name}.SC2Replay"
        new_path = replay_path.parent / new_name
        
        # Backup if requested
        if config.BACKUP_ORIGINALS:
            self.backup_replay(replay_path)
            
        # Rename file
        try:
            replay_path.rename(new_path)
            print(f"✅ Renamed: {filename} → {new_name}")
            self.stats['processed'] += 1
            
            # Handle .processed marker file
            processed_file = replay_path.parent / f"{base_name}.processed"
            if processed_file.exists():
                new_processed = replay_path.parent / f"{file_date}_{result}_vs_{opponent_race}_{base_name}.processed"
                processed_file.rename(new_processed)
                
        except Exception as e:
            print(f"❌ Error renaming {filename}: {e}")
            self.stats['errors'] += 1
            
    def process_all_replays(self):
        """Process all replay files in directory"""
        replay_files = list(self.replay_dir.glob("*.SC2Replay"))
        total_files = len(replay_files)
        
        print(f"\n📁 Found {total_files} replay files in {self.replay_dir}")
        print(f"🎮 Looking for player: {self.player_name}\n")
        
        for i, replay_path in enumerate(replay_files, 1):
            print(f"[{i}/{total_files}] Processing {replay_path.name}...")
            self.rename_replay(replay_path)
            
    def generate_report(self):
        """Generate and display statistics report"""
        if not config.GENERATE_REPORT:
            return
            
        total_games = self.stats['wins'] + self.stats['losses']
        
        print("\n" + "="*50)
        print("📊 REPLAY PROCESSING REPORT")
        print("="*50)
        print(f"Files processed: {self.stats['processed']}")
        print(f"Files skipped: {self.stats['skipped']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"\n📈 GAME STATISTICS")
        print(f"Total games analyzed: {total_games}")
        
        if total_games > 0:
            win_rate = (self.stats['wins'] / total_games) * 100
            print(f"Wins: {self.stats['wins']} ({win_rate:.1f}%)")
            print(f"Losses: {self.stats['losses']} ({100-win_rate:.1f}%)")
            print(f"\n🎯 MATCHUP BREAKDOWN")
            print(f"vs Terran: {self.stats['vs_Terran']}")
            print(f"vs Protoss: {self.stats['vs_Protoss']}")
            print(f"vs Zerg: {self.stats['vs_Zerg']}")
        print("="*50)

def main():
    print("🚀 StarCraft 2 Replay Renamer")
    print("="*50)
    
    # Check configuration
    if config.SC2_USERNAME == "YourUsername":
        print("❌ ERROR: Please update your SC2 username in config.py!")
        return
        
    if not os.path.exists(config.REPLAYS_PATH):
        print(f"❌ ERROR: Replay directory not found: {config.REPLAYS_PATH}")
        print("Please update the path in config.py")
        return
        
    # Create renamer instance
    renamer = SC2ReplayRenamer(config.SC2_USERNAME, config.REPLAYS_PATH)
    
    # Process replays
    renamer.process_all_replays()
    
    # Generate report
    renamer.generate_report()
    
    print("\n✅ Processing complete!")
    
if __name__ == "__main__":
    main()