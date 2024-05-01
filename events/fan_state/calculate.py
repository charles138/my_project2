from app.utils.convert_to_integer import convert_tag_value_to_int
from jobs.na_to_normalized_mapping.events.fan_state import main_fans_state_tags


def _calculate_main_fans_state_id(new_tag_value, log):
    if new_tag_value == 2:
        return 0
    elif new_tag_value == 3:
        return 2
    elif new_tag_value == 6:
        return 4
    elif new_tag_value == 10:
        return 10

    log.error('No main fans state id could be calculated')
    return None


def _calculate_gco_fans_state_id(new_tag_value, log):
    if new_tag_value == 1:
        return 4
    elif new_tag_value == 0:
        return 6

    log.error('No gco fans state id could be calculated')
    return None

def calculate_main_fans_state_event(event, log):
    log.debug('Calculating main fans state event')
    parts = event.get('id').split('.')

    if len(parts) != 3 or parts[2] not in main_fans_state_tags:
        return None

    tag_value = event.get('v')

    state_id = _calculate_main_fans_state_id(convert_tag_value_to_int(tag_value), log)

    log.debug(f'Main fans state state id calculated: {state_id}')

    if state_id is None:
        return None

    return {
        'id': 'MainFansState',
        'v': state_id,
        't': event.get('t'),
    }


def calculate_gco_fan_state_event(event, log):
    log.debug('Calculating gco fans state event')
    parts = event.get('id').split('.')

    if len(parts) != 3 or parts[2] not in main_fans_state_tags:
        return None

    tag_value = event.get('v')

    state_id = _calculate_gco_fans_state_id(convert_tag_value_to_int(tag_value), log)

    log.debug(f'gco fans state state id calculated: {state_id}')

    if state_id is None:
        return None

    return {
        'id': 'RecircFanState',
        'v': state_id,
        't': event.get('t'),
    }
