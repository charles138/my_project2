from app.utils.convert_to_integer import convert_tag_value_to_int
from jobs.na_to_normalized_mapping.events.climate_state import climate_system_state_tags


def _calculate_climate_system_state_id(new_tag_value, log):
    if new_tag_value == 2:
        return 1
    elif new_tag_value == 3:
        return 2
    elif new_tag_value == 6:
        return 4
    log.error('No climate system state id could be calculated')
    return None


def calculate_climate_system_state_event(event, log):
    parts = event.get('id').split('.')

    if len(parts) != 3 or parts[2] not in climate_system_state_tags:
        return None

    tag_value = event.get('v')

    state_id = _calculate_climate_system_state_id(convert_tag_value_to_int(tag_value), log)

    if state_id is None:
        return None

    return {
        'id': 'ClimateSystemState',
        'v': state_id,
        't': event.get('t'),
    }
