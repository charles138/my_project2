from databrix.common.cosmos import create_or_upsert

from app.utils.convert_to_integer import convert_tag_value_to_int
from jobs.na_to_normalized_mapping.cosmos import get_item_from_tmp_cosmos_container
from jobs.na_to_normalized_mapping.events.alarm_state import alarm_state_tags


def convert_decimal_to_binary_array(input_dec):
    out_str = f'{int(input_dec):016b}'

    return list(out_str)


def get_alarm_indices(input_list):
    out_list = []
    for ix, i in enumerate(input_list):
        if int(i) == 1:
            out_list.append(15 - ix)

    return out_list


def generate_alarm_id(fault_id, alarm_index):
    if int(alarm_index) < 10:
        alarm_index = f'0{alarm_index}'

    return int(f'1{fault_id}{alarm_index}')


def find_empty_alarm_spot(item):
    for i in range(0, 10):
        if f'AlarmNumber_{i}' not in item:
            return f'AlarmNumber_{i}'

    return None


def find_alarm_spot(item, alarm_id):
    for i in range(0, 10):
        if item.get(f'AlarmNumber_{i}') == alarm_id:
            return f'AlarmNumber_{i}'

    return None


def clean_alarm_spots(item):
    for i in range(0, 10):
        if f'AlarmNumber_{i}' in item and item.get(f'AlarmNumber_{i}') == 0:
            item.pop(f'AlarmNumber_{i}')

    return item


def calculate_alarm_state_id(item, new_tag, new_tag_value, log):
    log.debug(f'Calculating alarm state id. New tag value {convert_tag_value_to_int(new_tag_value)}')

    return_value = []

    fault_id = new_tag.split('_')[1]

    bits = convert_decimal_to_binary_array(new_tag_value)
    bits.reverse()

    for idx, bit in enumerate(bits):
        alarm_id = generate_alarm_id(fault_id, idx)
        alarm_spot = find_alarm_spot(item, alarm_id)

        if not alarm_spot and int(bit) == 1:
            # New alarm
            empty_alarm_spot = find_empty_alarm_spot(item)

            if empty_alarm_spot is None:
                log.error('No empty spot found')
                continue

            item[empty_alarm_spot] = alarm_id

            return_value.append({
                'event_id': empty_alarm_spot,
                'alarm_id': alarm_id,
            })
        elif alarm_spot and int(bit) == 0:
            # Alarm disabled
            item[alarm_spot] = 0

            return_value.append({
                'event_id': alarm_spot,
                'alarm_id': 0,
            })

    return return_value


def calculate_alarm_events(event, machine_id, container, log):
    return_events = []

    parts = event.get('id').split('.')

    if len(parts) != 3 or parts[2] not in alarm_state_tags:
        return None

    tag = parts[2]
    tag_value = event.get('v')

    item = get_item_from_tmp_cosmos_container(container=container, machine_id=machine_id, item_type='alarm')

    item[tag] = convert_tag_value_to_int(tag_value)

    result = calculate_alarm_state_id(item, tag, item[tag], log)

    for row in result:
        item[row['event_id']] = row['alarm_id']

        return_events.append({
            'id': row['event_id'],
            'v': row['alarm_id'],
            't': event.get('t'),
        })

    item = clean_alarm_spots(item)

    create_or_upsert(container=container, item=item)

    return return_events
