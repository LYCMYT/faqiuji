"""Explicit engineering role/route review; never infer process from a display name."""


def validate_part_roles(parts, roles, route_document):
    indexed = {part['part_id']: part for part in parts}
    reviewed = roles['parts']
    routes = route_document['routes']
    categories = route_document['route_categories']
    if len(indexed) != len(parts) or any(set(items) != set(indexed) for items in (reviewed, routes, categories)):
        raise ValueError('Part, role and route IDs must match exactly without duplicates')
    if roles['manufacturing_release'] is not False:
        raise ValueError('Role review does not authorize manufacturing release')
    for part_id, part in indexed.items():
        review = reviewed[part_id]
        if categories[part_id] not in roles['allowed_route_categories'].get(review['role'], []):
            raise ValueError(f'{part_id}: route category does not implement role {review["role"]}')
        if review['source_name'] != part['name'] or review['source_function'] != part['function']:
            raise ValueError(f'{part_id}: source name/function changed; engineering review required')
        if categories[part_id] != review['route_category']:
            raise ValueError(f'{part_id}: route category incompatible with reviewed role {review["role"]}')
        if routes[part_id] != review['reviewed_route']:
            raise ValueError(f'{part_id}: route text changed; engineering review required')
        if not review['role'] or not review['engineering_review_note']:
            raise ValueError(f'{part_id}: missing explicit role or engineering judgment')
