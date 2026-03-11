"""
📍 Сервис геолокации MAXXPHARM CRM
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from ..models.database import Location, User, Order
from ..config import settings


class LocationService:
    """Сервис для работы с геолокацией"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save_location(
        self,
        user_id: int,
        latitude: float,
        longitude: float,
        accuracy: Optional[float] = None,
        speed: Optional[float] = None,
        heading: Optional[float] = None,
        order_id: Optional[int] = None,
        address: Optional[str] = None
    ) -> Location:
        """Сохранение геолокации"""
        
        location = Location(
            user_id=user_id,
            order_id=order_id,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            speed=speed,
            heading=heading,
            address=address
        )
        
        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        
        return location
    
    async def get_user_locations(
        self,
        user_id: int,
        limit: int = 100,
        hours: int = 24
    ) -> List[Location]:
        """Получение геолокаций пользователя"""
        
        # Временной фильтр
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.session.execute(
            select(Location)
            .where(
                and_(
                    Location.user_id == user_id,
                    Location.created_at >= time_threshold
                )
            )
            .order_by(Location.created_at.desc())
            .limit(limit)
        )
        
        return result.scalars().all()
    
    async def get_last_location(self, user_id: int) -> Optional[Location]:
        """Получение последней геолокации пользователя"""
        
        result = await self.session.execute(
            select(Location)
            .where(Location.user_id == user_id)
            .order_by(Location.created_at.desc())
            .limit(1)
        )
        
        return result.scalar_one_or_none()
    
    async def get_courier_locations(self) -> List[Dict[str, Any]]:
        """Получение геолокаций всех курьеров"""
        
        # Получаем всех курьеров
        from ..models.database import UserRole
        courier_result = await self.session.execute(
            select(User).where(User.role == UserRole.COURIER.value, User.is_active == True)
        )
        couriers = courier_result.scalars().all()
        
        courier_locations = []
        
        for courier in couriers:
            last_location = await self.get_last_location(courier.id)
            
            if last_location:
                # Получаем активные заказы курьера
                from ..models.database import OrderStatus
                orders_result = await self.session.execute(
                    select(Order).where(
                        and_(
                            Order.courier_id == courier.id,
                            Order.status == OrderStatus.IN_DELIVERY.value
                        )
                    )
                )
                active_orders = orders_result.scalars().all()
                
                courier_locations.append({
                    'courier_id': courier.id,
                    'courier_name': courier.full_name,
                    'courier_phone': courier.phone,
                    'latitude': float(last_location.latitude),
                    'longitude': float(last_location.longitude),
                    'accuracy': last_location.accuracy,
                    'speed': last_location.speed,
                    'heading': last_location.heading,
                    'last_update': last_location.created_at,
                    'address': last_location.address,
                    'active_orders_count': len(active_orders),
                    'active_orders': [
                        {
                            'order_number': order.order_number,
                            'delivery_address': order.delivery_address
                        }
                        for order in active_orders
                    ]
                })
        
        return courier_locations
    
    async def get_route_history(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[Location]:
        """Получение истории маршрута пользователя"""
        
        result = await self.session.execute(
            select(Location)
            .where(
                and_(
                    Location.user_id == user_id,
                    Location.created_at >= start_date,
                    Location.created_at <= end_date
                )
            )
            .order_by(Location.created_at.asc())
        )
        
        return result.scalars().all()
    
    async def calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Расчет расстояния между двумя точками в километрах"""
        
        from math import radians, cos, sin, asin, sqrt
        
        # Переводим в радианы
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Формула Хаверсина
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Радиус Земли в километрах
        r = 6371
        
        return c * r
    
    async def get_daily_distance(self, user_id: int, date: datetime) -> float:
        """Расчет пройденного расстояния за день"""
        
        # Получаем геолокации за день
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        locations = await self.get_route_history(user_id, start_of_day, end_of_day)
        
        if len(locations) < 2:
            return 0.0
        
        total_distance = 0.0
        
        for i in range(len(locations) - 1):
            loc1 = locations[i]
            loc2 = locations[i + 1]
            
            distance = await self.calculate_distance(
                float(loc1.latitude),
                float(loc1.longitude),
                float(loc2.latitude),
                float(loc2.longitude)
            )
            
            # Добавляем расстояние, если оно разумное (не более 50 км за одну точку)
            if distance <= 50.0:
                total_distance += distance
        
        return total_distance
    
    async def get_delivery_time_estimate(
        self,
        courier_lat: float,
        courier_lon: float,
        delivery_lat: float,
        delivery_lon: float
    ) -> Dict[str, Any]:
        """Расчет примерного времени доставки"""
        
        # Расчет расстояния
        distance = await self.calculate_distance(
            courier_lat, courier_lon,
            delivery_lat, delivery_lon
        )
        
        # Средняя скорость курьера в городе (км/ч)
        avg_speed = 30.0
        
        # Время в пути (минуты)
        travel_time = (distance / avg_speed) * 60
        
        # Дополнительное время (прогрузка, поиск адреса)
        additional_time = 15
        
        # Общее время
        total_time = travel_time + additional_time
        
        return {
            'distance_km': round(distance, 2),
            'travel_time_minutes': round(travel_time),
            'additional_time_minutes': additional_time,
            'total_time_minutes': round(total_time),
            'estimated_arrival': datetime.utcnow() + timedelta(minutes=total_time)
        }
    
    async def cleanup_old_locations(self, days: int = 30) -> int:
        """Очистка старых геолокаций"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        from sqlalchemy import delete
        
        delete_result = await self.session.execute(
            delete(Location).where(Location.created_at < cutoff_date)
        )
        
        await self.session.commit()
        
        return delete_result.rowcount
    
    async def get_location_statistics(self) -> Dict[str, Any]:
        """Получение статистики геолокаций"""
        
        # Общее количество геолокаций
        total_result = await self.session.execute(select(func.count(Location.id)))
        total_locations = total_result.scalar()
        
        # Геолокации за сегодня
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_result = await self.session.execute(
            select(func.count(Location.id))
            .where(Location.created_at >= today)
        )
        today_locations = today_result.scalar()
        
        # Активные курьеры (с геолокацией за последний час)
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        active_couriers = await self.get_courier_locations()
        active_couriers_count = len([
            courier for courier in active_couriers
            if courier['last_update'] >= hour_ago
        ])
        
        return {
            'total_locations': total_locations,
            'today_locations': today_locations,
            'active_couriers': active_couriers_count,
            'total_couriers': len(active_couriers)
        }
    
    async def geocode_address(self, address: str) -> Optional[Dict[str, Any]]:
        """Геокодирование адреса в координаты"""
        
        if not settings.google_maps_api_key:
            return None
        
        try:
            import googlemaps
            
            gmaps = googlemaps.Client(key=settings.google_maps_api_key)
            
            # Геокодирование
            geocode_result = gmaps.geocode(address)
            
            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                
                return {
                    'latitude': location['lat'],
                    'longitude': location['lng'],
                    'formatted_address': geocode_result[0]['formatted_address'],
                    'place_id': geocode_result[0]['place_id']
                }
                
        except Exception as e:
            # Логирование ошибки
            print(f"Geocoding error: {e}")
        
        return None
    
    async def reverse_geocode(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[str]:
        """Обратное геокодирование (координаты в адрес)"""
        
        if not settings.google_maps_api_key:
            return None
        
        try:
            import googlemaps
            
            gmaps = googlemaps.Client(key=settings.google_maps_api_key)
            
            # Обратное геокодирование
            reverse_result = gmaps.reverse_geocode((latitude, longitude))
            
            if reverse_result:
                return reverse_result[0]['formatted_address']
                
        except Exception as e:
            # Логирование ошибки
            print(f"Reverse geocoding error: {e}")
        
        return None


# Функция для получения сервиса
async def get_location_service() -> LocationService:
    """Получение экземпляра LocationService"""
    from ..database import get_db
    
    async for session in get_db():
        return LocationService(session)
