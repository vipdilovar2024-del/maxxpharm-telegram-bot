#!/usr/bin/env python3
"""
🧠 AI Diagnostics Module - Умный анализ ошибок и рекомендаций
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class AIDiagnostics:
    def __init__(self, openai_client=None):
        self.openai_client = openai_client
        self.logger = logging.getLogger("ai_diagnostics")
        self.diagnostic_history = []
        
    async def analyze_error(self, error_data: Dict[str, Any]) -> Dict[str, Any]:
        """AI анализ ошибки с генерацией рекомендаций"""
        if not self.openai_client:
            return self._fallback_analysis(error_data)
        
        try:
            # Формируем промпт для AI
            prompt = self._create_analysis_prompt(error_data)
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты AI DevOps эксперт по диагностике Telegram ботов. Анализируй ошибки и давай конкретные решения."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            ai_response = response.choices[0].message.content
            
            # Парсим ответ AI
            analysis = self._parse_ai_response(ai_response)
            
            # Сохраняем в историю
            self.diagnostic_history.append({
                'timestamp': datetime.now(),
                'error_id': error_data.get('timestamp'),
                'analysis': analysis
            })
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ AI analysis failed: {e}")
            return self._fallback_analysis(error_data)
    
    def _create_analysis_prompt(self, error_data: Dict[str, Any]) -> str:
        """Создание промпта для анализа ошибки"""
        return f"""
Проанализируй ошибку Telegram бота и дай рекомендации:

ТИП ОШИБКИ: {error_data.get('error_type', 'Unknown')}
СООБЩЕНИЕ: {error_data.get('error_message', 'No message')}
КОНТЕКСТ: {error_data.get('context', 'No context')}
ВРЕМЯ: {error_data.get('timestamp', 'Unknown')}

TRACEBACK:
{error_data.get('traceback', 'No traceback')[:500]}

Дай ответ в формате JSON:
{{
    "severity": "low|medium|high|critical",
    "root_cause": "основная причина",
    "immediate_action": "немедленное действие",
    "prevention": "как предотвратить",
    "impact": "влияние на систему"
}}
"""
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Парсинг ответа от AI"""
        try:
            # Ищем JSON в ответе
            start = ai_response.find('{')
            end = ai_response.rfind('}') + 1
            
            if start != -1 and end != 0:
                json_str = ai_response[start:end]
                return json.loads(json_str)
            else:
                # Если JSON не найден, создаем структуру из текста
                return self._extract_from_text(ai_response)
                
        except json.JSONDecodeError:
            return self._extract_from_text(ai_response)
    
    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """Извлечение данных из текста если JSON не найден"""
        return {
            'severity': 'medium',
            'root_cause': 'AI анализ недоступен',
            'immediate_action': 'Проверить логи и перезапустить',
            'prevention': 'Улучшить обработку ошибок',
            'impact': 'Нужно ручное вмешательство',
            'raw_response': text
        }
    
    def _fallback_analysis(self, error_data: Dict[str, Any]) -> Dict[str, Any]:
        """Запасной анализ без AI"""
        error_type = error_data.get('error_type', '')
        error_msg = error_data.get('error_message', '')
        
        # Базовые правила для известных ошибок
        if 'TelegramConflictError' in error_type:
            return {
                'severity': 'high',
                'root_cause': 'Два экземпляра бота работают одновременно',
                'immediate_action': 'Остановить старый экземпляр',
                'prevention': 'Использовать Instance Lock',
                'impact': 'Бот не получает сообщения'
            }
        elif 'timeout' in error_msg.lower():
            return {
                'severity': 'medium',
                'root_cause': 'Превышено время ожидания сети/API',
                'immediate_action': 'Проверить подключение к сети',
                'prevention': 'Добавить retry механизм',
                'impact': 'Временные сбои в работе'
            }
        else:
            return {
                'severity': 'medium',
                'root_cause': 'Неизвестная ошибка',
                'immediate_action': 'Проверить логи',
                'prevention': 'Улучшить логирование',
                'impact': 'Нужна диагностика'
            }
    
    async def generate_health_report(self, system_data: Dict[str, Any]) -> str:
        """Генерация отчета о здоровье системы"""
        if not self.openai_client:
            return self._fallback_health_report(system_data)
        
        try:
            prompt = f"""
Создай отчет о здоровье Telegram CRM системы:

ДАННЫЕ СИСТЕМЫ:
{json.dumps(system_data, indent=2, default=str)}

ИСТОРИЯ ДИАГНОСТИКИ:
{len(self.diagnostic_history)} анализов ошибок

Создай краткий отчет с рекомендациями по улучшению.
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты AI системный аналитик. Создавай понятные отчеты о здоровье систем."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=800,
                temperature=0.5
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"❌ Health report generation failed: {e}")
            return self._fallback_health_report(system_data)
    
    def _fallback_health_report(self, system_data: Dict[str, Any]) -> str:
        """Запасной отчет о здоровье системы"""
        health_score = system_data.get('health_score', 0)
        error_count = system_data.get('total_errors', 0)
        
        report = f"""
📊 <b>Отчет о здоровье системы</b>

🔋 <b>Общая оценка:</b> {health_score}/100
📈 <b>Статус:</b> {'🟢 Отлично' if health_score > 80 else '🟡 Хорошо' if health_score > 60 else '🔴 Требует внимания'}

📊 <b>Метрики:</b>
• Ошибок за 24ч: {error_count}
• Активных пользователей: {system_data.get('active_users', 0)}
• Обработано сообщений: {system_data.get('messages_processed', 0)}

💡 <b>Рекомендации:</b>
• {'Система работает стабильно' if health_score > 80 else 'Требуется оптимизация'}
• {'Продолжайте мониторинг' if error_count < 5 else 'Проанализируйте частые ошибки'}
• {'Масштабируйте при необходимости' if system_data.get('active_users', 0) > 100 else 'Текущая нагрузка нормальная'}

🕐 <b>Время генерации:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report.strip()
