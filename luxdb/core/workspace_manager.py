
"""
Workspace Manager - zarządza plikami tworzonymi dynamicznie przez Beings
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import ulid

class WorkspaceManager:
    """Zarządza workspace'em dla plików tworzonych przez Beings"""
    
    def __init__(self, workspace_dir: str = "workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(exist_ok=True)
        self.changes_log = []
        self.sync_callbacks = []
    
    async def create_file(self, being_ulid: str, filename: str, content: str, file_type: str = "py") -> str:
        """Tworzy nowy plik w workspace"""
        
        # Stwórz folder dla Being'a
        being_dir = self.workspace_dir / being_ulid[:8]
        being_dir.mkdir(exist_ok=True)
        
        # Unikalna nazwa pliku
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{filename}_{timestamp}.{file_type}"
        file_path = being_dir / unique_filename
        
        # Zapisz plik
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Zaloguj zmianę
        change = {
            'id': str(ulid.ULID()),
            'being_ulid': being_ulid,
            'action': 'create_file',
            'file_path': str(file_path),
            'filename': unique_filename,
            'timestamp': datetime.now().isoformat(),
            'content_preview': content[:200] + '...' if len(content) > 200 else content
        }
        
        self.changes_log.append(change)
        
        # Powiadom o zmianie
        await self._notify_change(change)
        
        return str(file_path)
    
    async def update_file(self, being_ulid: str, file_path: str, new_content: str) -> bool:
        """Aktualizuje istniejący plik"""
        try:
            file_path_obj = Path(file_path)
            
            # Sprawdź czy plik należy do workspace
            if not str(file_path_obj).startswith(str(self.workspace_dir)):
                raise ValueError("File outside workspace")
            
            # Backup poprzedniej wersji
            backup_path = file_path_obj.with_suffix(f".backup.{datetime.now().strftime('%H%M%S')}")
            if file_path_obj.exists():
                file_path_obj.rename(backup_path)
            
            # Zapisz nową wersję
            with open(file_path_obj, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # Zaloguj zmianę
            change = {
                'id': str(ulid.ULID()),
                'being_ulid': being_ulid,
                'action': 'update_file',
                'file_path': str(file_path_obj),
                'backup_path': str(backup_path),
                'timestamp': datetime.now().isoformat(),
                'content_preview': new_content[:200] + '...' if len(new_content) > 200 else new_content
            }
            
            self.changes_log.append(change)
            await self._notify_change(change)
            
            return True
        except Exception as e:
            print(f"❌ Error updating file: {e}")
            return False
    
    def get_changes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Pobiera ostatnie zmiany"""
        return self.changes_log[-limit:] if limit else self.changes_log
    
    def get_being_files(self, being_ulid: str) -> List[Dict[str, Any]]:
        """Pobiera pliki created przez konkretnego Being'a"""
        being_dir = self.workspace_dir / being_ulid[:8]
        
        if not being_dir.exists():
            return []
        
        files = []
        for file_path in being_dir.iterdir():
            if file_path.is_file():
                files.append({
                    'path': str(file_path),
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'created': datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        
        return files
    
    async def _notify_change(self, change: Dict[str, Any]):
        """Powiadamia o zmianie"""
        print(f"📁 Workspace change: {change['action']} by {change['being_ulid'][:8]}")
        
        # Wywołaj callbacks
        for callback in self.sync_callbacks:
            try:
                await callback(change)
            except Exception as e:
                print(f"❌ Callback error: {e}")
    
    def add_sync_callback(self, callback):
        """Dodaje callback dla synchronizacji"""
        self.sync_callbacks.append(callback)
    
    def export_workspace(self) -> Dict[str, Any]:
        """Eksportuje cały workspace do JSONa"""
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'changes_count': len(self.changes_log),
            'beings': {}
        }
        
        for being_dir in self.workspace_dir.iterdir():
            if being_dir.is_dir():
                being_ulid = being_dir.name
                export_data['beings'][being_ulid] = {
                    'files': self.get_being_files(being_ulid + '0' * (8 - len(being_ulid)))  # pad ULID
                }
        
        return export_data

# Globalna instancja
workspace_manager = WorkspaceManager()
