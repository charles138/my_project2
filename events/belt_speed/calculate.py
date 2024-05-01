from databrix.common.cosmos import create_or_upsert

from jobs.na_to_normalized_mapping.cosmos import get_item_from_tmp_cosmos_container
from jobs.na_to_normalized_mapping.events import belt_speed_tags
from jobs.na_to_normalized_mapping.events.belt_speed import BELT_DRV_RUN_CMD
from jobs.na_to_normalized_mapping.events.belt_speed import BELT_SPEED_EST
from jobs.na_to_normalized_mapping.events.belt_speed import BELT_SPEED_SP


def calculate_belt_speed_est(event, machine_id, container, log):
    parts = event.get('id').split('.')

    if len(parts) != 3 or parts[2] not in belt_speed_tags:
        return None

    tag = parts[2]
    tag_value = event.get('v')

    item = get_item_from_tmp_cosmos_container(container=container, machine_id=machine_id, item_type='belt_speed')

    belt_speed_est = _calculate_belt_speed_est(item, tag, tag_value, log)

    if tag == BELT_DRV_RUN_CMD:
        if tag_value in ['True', '1', 'true']:
            item[tag] = True

        if tag_value in ['False', '0', 'false']:
            item[tag] = False
    else:
        item[tag] = float(tag_value)

    create_or_upsert(container, item)

    if belt_speed_est is None:
        return None

    return {
        'id': BELT_SPEED_EST,
        'v': belt_speed_est,
        't': event.get('t'),
    }


def _calculate_belt_speed_est(item, new_tag, new_tag_value, log):
    log.debug(f'Calculating belt speed est. New tag value {new_tag_value}')
    new_item = None
    if new_tag == BELT_DRV_RUN_CMD:
        if new_tag_value in ['True', '1', 'true']:
            new_item = {**item, new_tag: True}

        if new_tag_value in ['False', '0', 'false']:
            new_item = {**item, new_tag: False}
    else:
        new_item = {**item, new_tag: float(new_tag_value)}

    log.debug('====== old item ======')
    log.debug(item)
    log.debug('====== new item ======')
    log.debug(new_item)

    belt_speed_sp = new_item.get(BELT_SPEED_SP, 0)
    belt_drv_run_cmd = new_item.get(BELT_DRV_RUN_CMD, False)

    if belt_drv_run_cmd:
        return belt_speed_sp
    else:
        return 0
