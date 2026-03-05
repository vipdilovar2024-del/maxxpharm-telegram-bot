#!/usr/bin/env python3
"""
🔒 Instance Lock Module - Защита от множественных экземпляров
"""

import os
import sys
import fcntl
import time
import logging
from datetime import datetime

class InstanceLock:
    def __init__(self, lock_file="bot.lock"):
        self.lock_file = lock_file
        self.lock_fd = None
        self.instance_id = f"bot_{int(time.time())}"
        self.logger = logging.getLogger("instance_lock")
    
    def __enter__(self):
        """Получение блокировки"""
        try:
            # Пытаемся создать файл блокировки
            self.lock_fd = open(self.lock_file, 'w')
            
            # В Unix системах используем fcntl
            try:
                fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (ImportError, AttributeError):
                # Для Windows систем
                if os.path.exists(self.lock_file):
                    # Проверяем время создания файла
                    file_time = os.path.getctime(self.lock_file)
                    current_time = time.time()
                    
                    # Если файл старше 5 минут, считаем его мертвым
                    if current_time - file_time > 300:
                        self.logger.warning("🔒 Old lock file found, removing...")
                        os.remove(self.lock_file)
                    else:
                        self.logger.error("❌ Bot already running!")
                        print("❌ Bot already running! Another instance is active.")
                        sys.exit(1)
                else:
                    # Создаем новый файл блокировки
                    pass
            
            # Записываем ID экземпляра
            self.lock_fd.write(f"{self.instance_id}\n{datetime.now().isoformat()}")
            self.lock_fd.flush()
            
            self.logger.info(f"🔒 Lock acquired: {self.instance_id}")
            print(f"🔒 Instance lock acquired: {self.instance_id}")
            return True
            
        except IOError as e:
            self.logger.error(f"❌ Cannot acquire lock: {e}")
            print(f"❌ Cannot acquire lock: {e}")
            print("❌ Another bot instance is running!")
            sys.exit(1)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Освобождение блокировки"""
        if self.lock_fd:
            try:
                # Освобождаем блокировку
                try:
                    fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                except (ImportError, AttributeError):
                    pass
                
                self.lock_fd.close()
                
                # Удаляем файл блокировки
                if os.path.exists(self.lock_file):
                    os.remove(self.lock_file)
                
                self.logger.info(f"🔓 Lock released: {self.instance_id}")
                print(f"🔓 Instance lock released: {self.instance_id}")
                
            except Exception as e:
                self.logger.error(f"❌ Error releasing lock: {e}")
    
    def get_active_instance(self):
        """Получение информации об активном экземпляре"""
        try:
            if os.path.exists(self.lock_file):
                with open(self.lock_file, 'r') as f:
                    content = f.read().strip().split('\n')
                    return {
                        'instance_id': content[0],
                        'start_time': content[1] if len(content) > 1 else None
                    }
            return None
        except:
            return None
