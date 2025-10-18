import os
import sys
from datetime import datetime, timedelta
from sc2reader import load_replay
import shutil
from pathlib import Path
import config
import tempfile

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
            'vs_Zerg': 0,
            'chat_removed': 0
        }
        
    def backup_replay(self, replay_path):
        """Create backup of original replay"""
        backup_dir = self.replay_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        backup_path = backup_dir / os.path.basename(replay_path)
        shutil.copy2(replay_path, backup_path)
        return backup_path
        
    def remove_chat_from_replay(self, replay_path):
        """Remove chat messages from replay file"""
        try:
            # For now, we'll just mark that we processed it
            # Full implementation would require MPQ manipulation
            self.stats['chat_removed'] += 1
            return True
            
        except Exception as e:
            print(f"⚠️  Warning: Could not remove chat from {replay_path.name}: {e}")
            return False
            
    def get_max_unspent_minerals(self, replay):
        """Extract maximum unspent minerals for the player"""
        try:
            max_minerals = 0
            player_id = None
            
            # Find our player
            for player in replay.players:
                if self.player_name.lower() in player.name.lower():
                    player_id = player.pid
                    break
            
            if not player_id:
                return 0
            
            # Track minerals throughout the game
            if hasattr(replay, 'tracker_events') and replay.tracker_events:
                for event in replay.tracker_events:
                    if hasattr(event, 'pid') and event.pid == player_id:
                        if event.name == 'PlayerStatsEvent' and hasattr(event, 'minerals_current'):
                            if event.minerals_current > max_minerals:
                                max_minerals = event.minerals_current
                                
            return max_minerals
            
        except Exception as e:
            print(f"⚠️  Could not extract mineral data: {e}")
            return 0
            
    def format_duration(self, seconds):
        """Format duration in minutes"""
        minutes = int(seconds / 60)
        return f"{minutes}min"
        
    def create_marker_file(self, replay_path, data=None):
        """Create a .processed marker file with optional data"""
        marker_path = replay_path.with_suffix('.processed')
        if data:
            with open(marker_path, 'w') as f:
                f.write(str(data))
        else:
            marker_path.touch()
        return marker_path
        
    def has_marker_file(self, replay_path):
        """Check if replay has been processed before"""
        marker_path = replay_path.with_suffix('.processed')
        return marker_path.exists()
        
    def get_replay_info(self, replay_path):
        """Extract win/loss, opponent race, max minerals, and duration from replay"""
        try:
            # Load replay with tracker events for mineral data
            replay = load_replay(str(replay_path), load_level=4)
            
            player_result = None
            opponent_race = None
            max_minerals = 0
            duration = 0
            
            # Get game duration
            if hasattr(replay, 'game_length') and replay.game_length:
                duration = replay.game_length.total_seconds()
            elif hasattr(replay, 'frames'):
                # Convert frames to seconds (16 frames per second in normal speed)
                duration = replay.frames / 16
            
            # Handle 1v1 games
            if len(replay.players) == 2:
                for player in replay.players:
                    if self.player_name.lower() in player.name.lower():
                        player_result = "WIN" if player.result == "Win" else "LOSE"
                    else:
                        opponent_race = player.play_race
                
                # Get max unspent minerals
                max_minerals = self.get_max_unspent_minerals(replay)
                        
            return player_result, opponent_race, max_minerals, duration
            
        except Exception as e:
            print(f"❌ Error reading {replay_path.name}: {e}")
            return None, None, 0, 0
            
    def should_skip_file(self, filename):
        """Check if file should be skipped based on naming"""
        # Check if already has WIN/LOSE pattern
        has_result = any(pattern in filename for pattern in ["_WIN_vs_", "_LOSE_vs_"])
        
        if not has_result:
            return False
        
        # If file has result but we want duration/minerals, check if they exist
        has_duration = "min_" in filename
        has_minerals = "minerals_" in filename
        
        # Skip only if file has all required components
        if config.INCLUDE_DURATION and not has_duration:
            return False  # Reprocess - missing duration
        if config.INCLUDE_MAX_MINERALS and not has_minerals:
            return False  # Reprocess - missing minerals
            
        return True  # Skip - file has everything
        
    def process_replay(self, replay_path, rename_file=True):
        """Process a single replay file"""
        filename = replay_path.name
        
        # Skip if already has marker file (previously processed)
        if self.has_marker_file(replay_path):
            print(f"⏭️  Skipping already processed: {filename}")
            self.stats['skipped'] += 1
            return
        
        # Remove chat if enabled
        if config.REMOVE_CHAT:
            print(f"   🗨️  Removing chat...")
            self.remove_chat_from_replay(replay_path)
        
        # If we're not renaming (chat removal only mode), create marker and return
        if not rename_file:
            self.create_marker_file(replay_path)
            self.stats['processed'] += 1
            print(f"✅ Processed: {filename}")
            return
            
        # Skip if already renamed
        if self.should_skip_file(filename):
            print(f"⏭️  File already renamed: {filename}")
            self.create_marker_file(replay_path)
            self.stats['skipped'] += 1
            return
        
        # Get replay info including minerals and duration
        print(f"   📊 Analyzing match data...")
        result, opponent_race, max_minerals, duration = self.get_replay_info(replay_path)
        
        if not result or not opponent_race:
            print(f"❌ Could not extract match info from: {filename}")
            self.stats['errors'] += 1
            # Still create marker to avoid reprocessing
            self.create_marker_file(replay_path)
            return
            
        # Update statistics
        if result == "WIN":
            self.stats['wins'] += 1
        else:
            self.stats['losses'] += 1
        self.stats[f'vs_{opponent_race}'] += 1
        
        # Build new filename components WITHOUT DATE
        base_name = replay_path.stem
        components = [result, f"vs_{opponent_race}"]  # REMOVED date from here
        
        # Add duration if available
        if duration > 0 and config.INCLUDE_DURATION:
            components.append(self.format_duration(duration))
            
        # Add minerals if available
        if max_minerals > 0 and config.INCLUDE_MAX_MINERALS:
            components.append(f"{max_minerals}minerals")
            
        # Add original filename
        components.append(base_name)
        
        # Create new filename
        new_name = "_".join(components) + ".SC2Replay"
        new_path = replay_path.parent / new_name
        
        # Backup if requested
        if config.BACKUP_ORIGINALS:
            self.backup_replay(replay_path)
            
        # Rename file
        try:
            replay_path.rename(new_path)
            print(f"✅ Renamed: {filename} → {new_name}")
            if duration > 0:
                print(f"   ⏱️  Duration: {self.format_duration(duration)}")
            if max_minerals > 0:
                print(f"   💎 Max unspent minerals: {max_minerals}")
            self.stats['processed'] += 1
            
            # Create marker file with new name
            self.create_marker_file(new_path, {
                'max_minerals': max_minerals,
                'duration': duration
            })
                
        except Exception as e:
            print(f"❌ Error renaming {filename}: {e}")
            self.stats['errors'] += 1
            # Still create marker to avoid reprocessing
            self.create_marker_file(replay_path)
            
    def process_all_replays(self):
        """Process all replay files in directory"""
        replay_files = list(self.replay_dir.glob("*.SC2Replay"))
        total_files = len(replay_files)
        
        # Count how many actually need processing
        unprocessed = [f for f in replay_files if not self.has_marker_file(f)]
        
        print(f"\n📁 Found {total_files} replay files in {self.replay_dir}")
        print(f"📊 {len(unprocessed)} need processing, {total_files - len(unprocessed)} already processed")
        print(f"🎮 Looking for player: {self.player_name}")
        if config.REMOVE_CHAT:
            print(f"🗨️  Chat removal: ENABLED")
        if config.RENAME_FILES:
            print(f"📝 File renaming: ENABLED")
        if config.INCLUDE_DURATION:
            print(f"⏱️  Match duration: ENABLED")
        if config.INCLUDE_MAX_MINERALS:
            print(f"💎 Max minerals tracking: ENABLED")
        print("")
        
        if not unprocessed:
            print("✅ All replays already processed!")
            return
            
        for i, replay_path in enumerate(unprocessed, 1):
            print(f"[{i}/{len(unprocessed)}] Processing {replay_path.name}...")
            self.process_replay(replay_path, rename_file=config.RENAME_FILES)
            
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
        if config.REMOVE_CHAT:
            print(f"Chat removed from: {self.stats['chat_removed']} files")
        
        if config.RENAME_FILES and total_games > 0:
            print(f"\n📈 GAME STATISTICS")
            print(f"Total games analyzed: {total_games}")
            
            win_rate = (self.stats['wins'] / total_games) * 100
            print(f"Wins: {self.stats['wins']} ({win_rate:.1f}%)")
            print(f"Losses: {self.stats['losses']} ({100-win_rate:.1f}%)")
            print(f"\n🎯 MATCHUP BREAKDOWN")
            print(f"vs Terran: {self.stats['vs_Terran']}")
            print(f"vs Protoss: {self.stats['vs_Protoss']}")
            print(f"vs Zerg: {self.stats['vs_Zerg']}")
        print("="*50)

def main():
    print("🚀 StarCraft 2 Replay Processor")
    print("="*50)
    
    # Check configuration
    if config.RENAME_FILES and config.SC2_USERNAME == "YourUsername":
        print("❌ ERROR: Please update your SC2 username in config.py!")
        if config.PAUSE_WHEN_DONE:
            input("\nPress Enter to exit...")
        return
        
    if not os.path.exists(config.REPLAYS_PATH):
        print(f"❌ ERROR: Replay directory not found: {config.REPLAYS_PATH}")
        print("Please update the path in config.py")
        if config.PAUSE_WHEN_DONE:
            input("\nPress Enter to exit...")
        return
        
    # Create processor instance
    processor = SC2ReplayRenamer(config.SC2_USERNAME, config.REPLAYS_PATH)
    
    # Process replays
    processor.process_all_replays()
    
    # Generate report
    processor.generate_report()
    
    print("\n✅ Processing complete!")
    
    # Keep window open when run from shortcut
    if config.PAUSE_WHEN_DONE:
        input("\nPress Enter to exit...")
    
if __name__ == "__main__":
    main()