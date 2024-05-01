from app.utils.convert_to_integer import convert_tag_value_to_int
from jobs.na_to_normalized_mapping.events.drive_state import drive_state_tags


def _calculate_drive_state_id(new_tag_value, log):
    if new_tag_value == 0:
        return 0
    elif new_tag_value == 2:
        return 1
    elif new_tag_value == 3:
        return 2
    elif new_tag_value == 8:
        return 10
    elif new_tag_value == 5:
        return 3
    elif new_tag_value == 6:
        return 4
    elif new_tag_value == 10:
        return 10

    log.error('No cleaning state id could be calculated')
    return None

def _calculate_gco_drive_state_id(new_tag_value, log):
    if new_tag_value == 1:
        return 4
    elif new_tag_value == 0:
        return 6

    log.error('No cleaning state id could be calculated')
    return None

def calculate_drive_event(event, log):
    parts = event.get('id').split('.')

    if len(parts) != 3 or parts[2] not in drive_state_tags:
        return None

    tag_value = event.get('v')

    state_id = _calculate_drive_state_id(convert_tag_value_to_int(tag_value), log)

    if state_id is None:
        return None

    return {
        'id': 'DriveSystem01State',
        'v': state_id,
        't': event.get('t'),
    }

def calculate_gco_drive_event(event, log):
    parts = event.get('id').split('.')

    if len(parts) != 3 or parts[2] not in drive_state_tags:
        return None

    tag_value = event.get('v')

    state_id = _calculate_gco_drive_state_id(convert_tag_value_to_int(tag_value), log)

    if state_id is None:
        return None

    return {
        'id': 'DriveSystem01State',
        'v': state_id,
        't': event.get('t'),
    }
