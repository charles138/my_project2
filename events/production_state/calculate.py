from databrix.common.cosmos import create_or_upsert

from app.utils.convert_to_integer import convert_tag_value_to_int
from jobs.na_to_normalized_mapping.cosmos import get_item_from_tmp_cosmos_container
from jobs.na_to_normalized_mapping.events.production_state import production_state_tags
from jobs.na_to_normalized_mapping.events.production_state import PS_CLEAN_MODE_RUNNING
from jobs.na_to_normalized_mapping.events.production_state import PS_COLD_KEEP_MD_RUNNING
from jobs.na_to_normalized_mapping.events.production_state import PS_COLD_STOR_MD_RUNNING
from jobs.na_to_normalized_mapping.events.production_state import PS_JBT_HEAT_RUN
from jobs.na_to_normalized_mapping.events.production_state import PS_JBT_MODE_HETA_RUN
from jobs.na_to_normalized_mapping.events.production_state import PS_JBT_MODE_RUNNING
from jobs.na_to_normalized_mapping.events.production_state import PS_JBT_MODE_STEAM_RUN
from jobs.na_to_normalized_mapping.events.production_state import PS_JBT_RUNNING
from jobs.na_to_normalized_mapping.events.production_state import PS_JBT_STEAM_RUN
from jobs.na_to_normalized_mapping.events.production_state import PS_MODE_STATUS_IND
from jobs.na_to_normalized_mapping.events.production_state import PS_PROD_MD_RUNNING

def calculate_production_event(event, machine_id, container, log, machine_id_gco,machine_id_tdo):
    parts = event.get('id').split('.')

    if len(parts) != 3 or parts[2] not in production_state_tags:
        log.debug('Not in production_state_tags')
        return None

    tag = parts[2]
    tag_value = event.get('v')

    item = get_item_from_tmp_cosmos_container(container=container, machine_id=machine_id, item_type='production_state')

    item[tag] = convert_tag_value_to_int(tag_value)

    if item['machine_id'] in machine_id_gco:
        state_id = _calculate_production_state_id_pna_gco(item, tag, tag_value, log)

    elif item['machine_id'] in machine_id_tdo:
        state_id = _calculate_production_state_id_pna_tdo(item, tag, tag_value, log)
    else:
        state_id = _calculate_production_state_id(item, tag, tag_value, log)

    create_or_upsert(container=container, item=item)

    if state_id is None:
        return None

    return {
        'id': 'ProductionState',
        'v': state_id,
        't': event.get('t'),
    }


def _calculate_production_state_id(item, new_tag, new_tag_value, log):
    log.debug(f'Calculating production state id. New tag {new_tag} value {convert_tag_value_to_int(new_tag_value)}')
    new_item = {**item, new_tag: convert_tag_value_to_int(new_tag_value)}

    clean_md_running = new_item.get(PS_CLEAN_MODE_RUNNING, 0)
    cold_keep_md_running = new_item.get(PS_COLD_KEEP_MD_RUNNING, 0)
    cold_stor_md_running = new_item.get(PS_COLD_STOR_MD_RUNNING, 0)
    prod_md_running = new_item.get(PS_PROD_MD_RUNNING, 0)
    mode_status_ind = new_item.get(PS_MODE_STATUS_IND, 0)

    if cold_keep_md_running == 0 \
            and cold_stor_md_running == 0 \
            and prod_md_running == 0 \
            and mode_status_ind == 0:
        return 1  # Idle

    if clean_md_running == 0 \
            and cold_keep_md_running == 0 \
            and cold_stor_md_running == 0 \
            and prod_md_running == 0 \
            and mode_status_ind != 0:
        return 5  # Stop

    if clean_md_running == 0 \
            and prod_md_running == 1:
        return 4  # Production Running

    if clean_md_running == 0 \
            and cold_keep_md_running == 1:
        return 4  # Cold Keep Mode Running

    if clean_md_running == 0 \
            and cold_stor_md_running == 1:
        return 4  # Cold Storage Mode Running

    return 1  # Idle


def _calculate_production_state_id_pna_gco(item, new_tag, new_tag_value, log):
    """
    Calculates and returns the production state ID for PNA GC Ovens based on the current mode.

    This function updates the production state ID based on the new tag values provided, focusing
    primarily on the different 'Run' modes of the oven. If any of the 'Run' modes (Heat, Steam, or General Running)
    are active, the oven is considered to be in 'Running' state. If none of the 'Run' modes are active,
    the oven is considered to be 'Idle'. This is used to update the operational status of the oven
    in real-time for monitoring and control purposes.

    Parameters:
        item (dict): The original dictionary containing the current states or modes of the oven.
        new_tag (str): The name of the tag that has been updated.
        new_tag_value (any): The new value of the updated tag.
        log (Logger): A logging object used for debugging and tracking.

    Returns:
        int: The new production state ID where:
             4 represents 'Running' state,
             1 represents 'Idle' state,
             5 represents 'Stop' state,
             None is returned if no specific conditions are met (fallback/default case).

    """

    log.debug(f'Calculating production state id. New Gco tag {new_tag} value {convert_tag_value_to_int(new_tag_value)}')

    new_tag_value=convert_tag_value_to_int(new_tag_value)
    new_item = {**item, new_tag: new_tag_value}

    # New logic for PNA GC Ovens
    JBT_Mode_Heat_Run = new_item.get(PS_JBT_MODE_HETA_RUN, 0)
    JBT_Mode_Steam_Run = new_item.get(PS_JBT_MODE_STEAM_RUN, 0)
    JBT_Mode_Running = new_item.get(PS_JBT_MODE_RUNNING, 0)
    mode_status_ind = new_item.get(PS_MODE_STATUS_IND, 0)



    # Check if any of the "Run" tags are true
    if JBT_Mode_Heat_Run or JBT_Mode_Steam_Run or JBT_Mode_Running or mode_status_ind!=0:
        return 4  # Running

    # Check if running tag are not true
    if new_tag == PS_JBT_MODE_RUNNING and new_tag_value==0:
        return 1  # Idle

    if new_tag == PS_MODE_STATUS_IND and new_tag_value==0:
        return 5  #Stop

    if not JBT_Mode_Heat_Run and not JBT_Mode_Steam_Run:
        return 5  #Stop

    return None  # This line is a fallback in case none of the conditions above are met



def _calculate_production_state_id_pna_tdo(item, new_tag, new_tag_value, log):
    """
    Calculates and returns the production state ID for PNA TDO based on the current mode.

    This function updates the production state ID based on the new tag values provided, focusing
    primarily on the different 'Run' modes of the oven. If any of the 'Run' modes (Heat, Steam, or General Running)
    are active, the oven is considered to be in 'Running' state. If none of the 'Run' modes are active,
    the oven is considered to be 'Idle'. This is used to update the operational status of the oven
    in real-time for monitoring and control purposes.

    Parameters:
        item (dict): The original dictionary containing the current states or modes of the oven.
        new_tag (str): The name of the tag that has been updated.
        new_tag_value (any): The new value of the updated tag.
        log (Logger): A logging object used for debugging and tracking.

    Returns:
        int: The new production state ID where:
             4 represents 'Running' state,
             1 represents 'Idle' state,
             5 represents 'Stop' state,
             None is returned if no specific conditions are met (fallback/default case).

    """

    log.debug(f'Calculating production state id. New Gco tag {new_tag} value {convert_tag_value_to_int(new_tag_value)}')

    new_tag_value=convert_tag_value_to_int(new_tag_value)
    new_item = {**item, new_tag: new_tag_value}

    # New logic for PNA TDO
    JBT_Mode_Heat_Run = new_item.get(PS_JBT_HEAT_RUN, 0)
    JBT_Mode_Steam_Run = new_item.get(PS_JBT_STEAM_RUN, 0)
    JBT_Mode_Running = new_item.get(PS_JBT_RUNNING, 0)

    # Check if any of the "Run" tags are true
    if JBT_Mode_Heat_Run or JBT_Mode_Steam_Run or JBT_Mode_Running:
        return 4  # Running

    # Check if running tag are not true
    if new_tag == PS_JBT_RUNNING and new_tag_value==0:
        return 1  # Idle

    if not JBT_Mode_Heat_Run and not JBT_Mode_Steam_Run:
        return 5  #Stop

    return None  # This line is a fallback in case none of the conditions above are met
