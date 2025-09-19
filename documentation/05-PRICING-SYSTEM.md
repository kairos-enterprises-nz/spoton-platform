# Scalable Pricing Implementation

## Overview

We've implemented a more scalable pricing system by creating a new `pricing` app within the `web_support` module. This new system replaces hardcoded pricing in the `address_plans/utils.py` file with a database-driven approach that uses pricing IDs for stable references to pricing data.

## Backend Changes

### New Django App: `web_support.pricing`

1. **Models:**
   - `ElectricityPlan`: Stores electricity pricing with support for Fixed, TOU, and Spot plans
   - `BroadbandPlan`: Stores broadband pricing with support for Fibre, Fixed Wireless, and Rural plans
   - `PricingRegion`: Manages service availability by geographic region

2. **API Endpoints:**
   - `/api/pricing/electricity/` - Get electricity plans for a city
   - `/api/pricing/broadband/` - Get broadband plans for a city
   - `/api/pricing/plan/{pricing_id}/` - Get specific plan by pricing ID
   - `/api/pricing/plans/bulk/` - Get multiple plans by pricing IDs
   - `/api/pricing/availability/` - Check service availability for a city
   - `/api/pricing/regions/` - List all available regions

3. **Data Migration:**
   - Management command `migrate_pricing_data` to transfer existing hardcoded pricing to database models

4. **Backwards Compatibility:**
   - Updated `address_summary` endpoint to try new pricing models first but fall back to legacy logic if needed
   - Maintained same plan IDs and JSON response structure

### Integration with Existing Backend

1. **Modified `address_plans/views.py`:**
   - Added support for retrieving plans from the new pricing models
   - Maintained backward compatibility with existing code

2. **Added to Django Settings:**
   - Added `web_support.pricing` to `INSTALLED_APPS`

3. **URL Configuration:**
   - Added pricing app URLs to the main urls.py

## Frontend Changes

1. **Enhanced Address Service:**
   - Added new API functions for retrieving pricing data using pricing IDs:
     - `getElectricityPlansByCity()`
     - `getBroadbandPlansByCity()`
     - `getPlanByPricingId()`

2. **Updated Plan Checker Component:**
   - Modified to use pricing_id for plan identification when available
   - Updated plan selection logic to work with both legacy and new pricing structure
   - Maintained backward compatibility for existing deployments

3. **Updated Onboarding Components:**
   - Enhanced to handle the new pricing ID system

## Benefits of the New System

1. **Scalability:** Pricing data can be updated without code changes
2. **Maintainability:** Clear separation between pricing logic and application code
3. **Flexibility:** Support for different pricing structures by city/region
4. **Stability:** Pricing IDs provide stable references even when pricing details change
5. **Admin Control:** Pricing can be managed through the Django admin interface

## Future Improvements

1. **Caching:** Add Redis caching for frequently accessed pricing data
2. **Versioning:** Implement pricing data versioning for historical tracking
3. **Bulk Import/Export:** Tools for bulk management of pricing data
4. **Analytics:** Track which plans are most viewed/selected
5. **A/B Testing:** Infrastructure for testing different pricing strategies
