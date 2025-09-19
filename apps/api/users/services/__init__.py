"""
User services package.

Contains business logic services for user management:
- UserCacheService: Smart caching for user data
"""

from .user_cache_service import UserCacheService

__all__ = ['UserCacheService']