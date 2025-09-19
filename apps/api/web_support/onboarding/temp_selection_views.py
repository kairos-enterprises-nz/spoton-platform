"""
Temporary selection storage for cross-domain data transfer
Handles saving service selection data before authentication for social signup
"""
import json
import uuid
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.core.cache import cache
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
@require_http_methods(["POST"])
def save_temp_selection(request):
    """
    Save temporary service selection data before authentication
    Used for social signup flow to preserve data across domains
    """
    try:
        data = json.loads(request.body)
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Add metadata
        selection_data = {
            'selectedAddress': data.get('selectedAddress'),
            'selectedServices': data.get('selectedServices'),
            'selectedPlans': data.get('selectedPlans'),
            'timestamp': data.get('timestamp', timezone.now().isoformat()),
            'provider': data.get('provider'),
            'action': data.get('action'),
            'expires_at': (timezone.now() + timedelta(hours=1)).isoformat()
        }
        
        # Store in cache with 1 hour expiry
        cache_key = f"temp_selection_{session_id}"
        cache.set(cache_key, selection_data, timeout=3600)  # 1 hour
        
        logger.info(f"💾 Saved temporary selection data with session ID: {session_id}")
        logger.info(f"📋 Selection data: {selection_data}")
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'message': 'Selection data saved successfully'
        })
        
    except json.JSONDecodeError:
        logger.error("❌ Invalid JSON in temp selection request")
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
        
    except Exception as e:
        logger.error(f"❌ Error saving temp selection: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to save selection data'
        }, status=500)


@method_decorator(csrf_exempt, name='dispatch') 
@require_http_methods(["GET"])
def get_temp_selection(request, session_id):
    """
    Retrieve temporary service selection data after authentication
    """
    try:
        cache_key = f"temp_selection_{session_id}"
        selection_data = cache.get(cache_key)
        
        if not selection_data:
            logger.warning(f"🔍 Temp selection not found for session ID: {session_id}")
            return JsonResponse({
                'success': False,
                'error': 'Selection data not found or expired'
            }, status=404)
        
        # Check expiry
        expires_at = datetime.fromisoformat(selection_data['expires_at'].replace('Z', '+00:00'))
        if timezone.now() > expires_at:
            logger.warning(f"⏰ Temp selection expired for session ID: {session_id}")
            cache.delete(cache_key)
            return JsonResponse({
                'success': False,
                'error': 'Selection data has expired'
            }, status=404)
        
        logger.info(f"📖 Retrieved temp selection for session ID: {session_id}")
        
        # Delete after retrieval to prevent reuse
        cache.delete(cache_key)
        
        return JsonResponse({
            'success': True,
            'data': selection_data
        })
        
    except Exception as e:
        logger.error(f"❌ Error retrieving temp selection: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to retrieve selection data'
        }, status=500)
