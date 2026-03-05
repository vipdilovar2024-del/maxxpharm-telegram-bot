#!/usr/bin/env python3
"""
📊 Error Monitor Module - Мониторинг и анализ ошибок
"""

import asyncio
import logging
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Any

class ErrorMonitor:
    def __init__(self):
        self.errors = deque(maxlen=100)  # Последние 100 ошибок
        self.error_patterns = defaultdict(int)
        self.critical_errors = []
        self.logger = logging.getLogger("error_monitor")
        
    def log_error(self, error: Exception, context: str = ""):
        """Логирование ошибки с анализом"""
        error_data = {
            'timestamp': datetime.now(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'traceback': self._get_traceback(error)
        }
        
        self.errors.append(error_data)
        self._analyze_error_pattern(error_data)
        
        # Проверяем на критические ошибки
        if self._is_critical_error(error_data):
            self.critical_errors.append(error_data)
            self.logger.critical(f"🚨 Critical error detected: {error_data['error_type']}")
        
        self.logger.error(f"❌ Error logged: {error_data['error_type']} - {error_data['error_message']}")
    
    def _get_traceback(self, error: Exception) -> str:
        """Получение traceback ошибки"""
        import traceback
        return ''.join(traceback.format_tb(error.__traceback__))
    
    def _analyze_error_pattern(self, error_data: Dict):
        """Анализ паттернов ошибок"""
        error_msg = error_data['error_message'].lower()
        
        # Определяем типы ошибок
        patterns = {
            'telegram_conflict': r'conflict.*terminated.*other.*getupdates',
            'network_error': r'connection.*timeout|network.*unreachable',
            'api_error': r'api.*error.*rate.*limit',
            'database_error': r'database.*connection.*failed',
            'openai_error': r'openai.*api.*error'
        }
        
        for pattern_name, pattern in patterns.items():
            if re.search(pattern, error_msg):
                self.error_patterns[pattern_name] += 1
    
    def _is_critical_error(self, error_data: Dict) -> bool:
        """Определение критических ошибок"""
        critical_types = [
            'TelegramConflictError',
            'DatabaseConnectionError',
            'AuthenticationError'
        ]
        
        return error_data['error_type'] in critical_types
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Получение сводки ошибок за период"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self.errors if e['timestamp'] > cutoff_time]
        
        return {
            'total_errors': len(recent_errors),
            'error_types': dict(Counter([e['error_type'] for e in recent_errors])),
            'error_patterns': dict(self.error_patterns),
            'critical_errors': len([e for e in recent_errors if self._is_critical_error(e)]),
            'most_common': self._get_most_common_errors(recent_errors),
            'time_range': f"Last {hours} hours"
        }
    
    def _get_most_common_errors(self, errors: List[Dict]) -> List[Dict]:
        """Получение самых частых ошибок"""
        error_counts = defaultdict(int)
        for error in errors:
            error_counts[error['error_type']] += 1
        
        return sorted(
            [{'type': k, 'count': v} for k, v in error_counts.items()],
            key=lambda x: x['count'],
            reverse=True
        )[:5]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Получение статуса здоровья системы"""
        recent_errors = [e for e in self.errors 
                       if e['timestamp'] > datetime.now() - timedelta(hours=1)]
        
        health_score = max(0, 100 - len(recent_errors) * 10)
        
        return {
            'health_score': health_score,
            'status': 'healthy' if health_score > 80 else 'degraded' if health_score > 50 else 'critical',
            'recent_errors': len(recent_errors),
            'last_error': self.errors[-1] if self.errors else None
        }

# Импортируем Counter для анализа
from collections import Counter
