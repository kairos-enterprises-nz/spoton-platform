"""
Django management command to test the user cache service.
"""

from django.core.management.base import BaseCommand
from users.services import UserCacheService

class Command(BaseCommand):
    help = 'Test the user cache service'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--keycloak-id',
            type=str,
            help='Test with specific Keycloak ID',
        )
    
    def handle(self, *args, **options):
        keycloak_id = options.get('keycloak_id')
        
        self.stdout.write("🧪 Testing UserCacheService...")
        
        # Test cache stats
        stats = UserCacheService.get_cache_stats()
        self.stdout.write(f"📊 Cache stats: {stats}")
        
        if keycloak_id:
            self.stdout.write(f"🔍 Testing with Keycloak ID: {keycloak_id}")
            
            # First call - should fetch from Keycloak
            self.stdout.write("First call (should fetch from Keycloak):")
            data1 = UserCacheService.get_user_data(keycloak_id)
            if data1:
                self.stdout.write(f"✅ Got data: {data1['email']} - cached at {data1.get('cache_timestamp')}")
            else:
                self.stdout.write("❌ No data returned")
                return
            
            # Second call - should use cache
            self.stdout.write("\nSecond call (should use cache):")
            data2 = UserCacheService.get_user_data(keycloak_id)
            if data2:
                self.stdout.write(f"✅ Got cached data: {data2['email']} - cached at {data2.get('cache_timestamp')}")
            else:
                self.stdout.write("❌ No cached data returned")
            
            # Test cache invalidation
            self.stdout.write("\n🗑️ Testing cache invalidation:")
            result = UserCacheService.invalidate_user_cache(keycloak_id)
            self.stdout.write(f"Cache invalidation result: {result}")
            
            # Third call - should fetch fresh after invalidation
            self.stdout.write("\nThird call (should fetch fresh after invalidation):")
            data3 = UserCacheService.get_user_data(keycloak_id)
            if data3:
                self.stdout.write(f"✅ Got fresh data: {data3['email']} - cached at {data3.get('cache_timestamp')}")
            else:
                self.stdout.write("❌ No fresh data returned")
        
        else:
            self.stdout.write("💡 Use --keycloak-id <id> to test with a real user")
        
        self.stdout.write("\n✅ Cache testing complete!")