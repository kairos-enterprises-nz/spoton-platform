# Pricing App

The Pricing app provides a scalable pricing system for electricity and broadband services. 
It replaces the hardcoded pricing in `address_plans/utils.py` with a database-driven approach.

## Key Features

- Separate models for electricity and broadband pricing
- Pricing IDs for stable references to pricing data
- Geographic pricing by city/region
- Support for multiple plan types and variations
- Admin interface for managing pricing data
- API endpoints for retrieving pricing information

## Models

### ElectricityPlan

Stores electricity pricing information with support for:
- Fixed Price plans
- Time of Use (TOU) plans
- Spot Price plans
- Standard and Low User variations

### BroadbandPlan

Stores broadband pricing information with support for:
- Fibre plans
- Fixed Wireless plans
- Rural plans
- Different data allowances and speeds

### PricingRegion

Manages service availability by geographic region with:
- City/region definitions
- Service availability flags (electricity, broadband, both)
- Display names for UI presentation

## API Endpoints

### Service Availability

- `GET /api/pricing/availability/?city=cityname` - Check availability for a city
- `GET /api/pricing/regions/` - List all available regions

### Plan Endpoints

- `GET /api/pricing/electricity/?city=cityname` - Get electricity plans for a city
- `GET /api/pricing/broadband/?city=cityname` - Get broadband plans for a city

### Pricing ID Based Endpoints

- `GET /api/pricing/plan/{pricing_id}/` - Get a specific plan by pricing ID
- `GET /api/pricing/plans/bulk/?pricing_ids=id1,id2,id3` - Get multiple plans by pricing IDs

## Data Migration

Use the management command to migrate existing hardcoded pricing data:

```
python manage.py migrate_pricing_data
```

Use `--dry-run` flag to preview changes without saving to database:

```
python manage.py migrate_pricing_data --dry-run
```

## Integration with Existing Code

The pricing app maintains backward compatibility with existing code by:

1. Keeping the same plan IDs (1, 2, 3 for electricity; 101, 102, 103 for broadband)
2. Providing backward-compatible utility functions (`get_electricity_plans`, `get_broadband_plans`)
3. Preserving the same JSON response structure in API endpoints

## Frontend Integration

Frontend components like PlanChecker.jsx have been updated to:
1. Use pricing_id for stable plan identification
2. Fall back to name-based identification for backward compatibility
3. Support new API endpoints for retrieving plan data
