from databrix.common.cosmos import create_or_upsert

from app.utils.convert_to_integer import convert_tag_value_to_int
from jobs.na_to_normalized_mapping.cosmos import get_item_from_tmp_cosmos_container
from jobs.na_to_normalized_mapping.events import cleaning_state_tags
from jobs.na_to_normalized_mapping.events.cleaning_state import CS_CIP_INSPECTION_PAUSE
from jobs.na_to_normalized_mapping.events.cleaning_state import CS_CLEAN_MODE_RUNNING
from jobs.na_to_normalized_mapping.events.cleaning_state import CS_CLEAN_MODE_SELECTED
from jobs.na_to_normalized_mapping.events.cleaning_state import CS_JBT_CIP_RUN
from jobs.na_to_normalized_mapping.events.cleaning_state import CS_JBT_COOLDOWN_RUN
from jobs.na_to_normalized_mapping.events.cleaning_state import CS_JBT_MODE_CIP_RUN
from jobs.na_to_normalized_mapping.events.cleaning_state import CS_JBT_MODE_COOLDOWN_RUN
from jobs.na_to_normalized_mapping.events.cleaning_state import CS_JBT_MODE_RINSE_RUN
from jobs.na_to_normalized_mapping.events.cleaning_state import CS_JBT_MODE_SOAK_RUN
from jobs.na_to_normalized_mapping.events.cleaning_state import CS_JBT_RINSE_RUN
from jobs.na_to_normalized_mapping.events.cleaning_state import CS_JBT_SOAK_RUN
from jobs.na_to_normalized_mapping.events.cleaning_state import CS_SYSTEM_MASTER_STOP
from jobs.na_to_normalized_mapping.events.cleaning_state import CS_SYSTEM_MASTER_STOP_PB
from jobs.na_to_normalized_mapping.events.cleaning_state import CS_SYSTEM_MASTER_STOP_SW


def calculate_cleaning_event(event, machine_id, container, log, machine_id_gco,machine_id_tdo):
    parts = event.get('id').split('.')

    if len(parts) != 3 or parts[2] not in cleaning_state_tags:
        return None

    tag = parts[2]
    tag_value = event.get('v')

    item = get_item_from_tmp_cosmos_container(container=container, machine_id=machine_id, item_type='cleaning_state')
    if item['machine_id'] in machine_id_gco:
        state_id = _calculate_cleaning_state_id_pna_gco(item, tag, tag_value, log)

    elif item['machine_id'] in machine_id_tdo:
        state_id = _calculate_cleaning_state_id_pna_tdo(item, tag, tag_value, log)

    else:
        state_id = _calculate_cleaning_state_id(item, tag, tag_value, log)

    item[tag] = convert_tag_value_to_int(tag_value)

    create_or_upsert(container=container, item=item)

    if state_id is None:
        return None

    return {
        'id': 'CleaningState',
        'v': state_id,
        't': event.get('t'),
    }


def _calculate_cleaning_state_id(item, new_tag, new_tag_value, log):
    log.debug(f'Calculating cleaning state id. New tag value {convert_tag_value_to_int(new_tag_value)}')
    new_item = {**item, new_tag: convert_tag_value_to_int(new_tag_value)}

    log.debug('====== old item ======')
    log.debug(item)
    log.debug('====== new item ======')
    log.debug(new_item)

    clean_md_running = new_item.get(CS_CLEAN_MODE_RUNNING, 0)
    clean_md_selected = new_item.get(CS_CLEAN_MODE_SELECTED, 0)
    system_master_stop = new_item.get(CS_SYSTEM_MASTER_STOP, 0)
    system_master_stop_pb = new_item.get(CS_SYSTEM_MASTER_STOP_PB, 0)
    system_master_stop_sw = new_item.get(CS_SYSTEM_MASTER_STOP_SW, 0)
    cip_inspection_pause = new_item.get(CS_CIP_INSPECTION_PAUSE, 0)

    if clean_md_running == 0 \
            and clean_md_selected == 1 \
            and system_master_stop_pb == 1 \
            and cip_inspection_pause == 0:
        return 5  # STOP

    if clean_md_running == 1 \
            and system_master_stop == 0 \
            and system_master_stop_pb == 0:
        return 4  # RUNNING

    if clean_md_selected == 1 \
            and clean_md_running == 0 \
            and system_master_stop == 1 \
            and cip_inspection_pause == 1:
        return 5  # STOP

    if clean_md_running == 0 \
            and clean_md_selected == 1:
        return 5  # STOP

    if clean_md_selected == 1 \
            and system_master_stop_sw == 1:
        return 5  # STOP

    if clean_md_selected == 1 \
            and system_master_stop == 1 \
            and cip_inspection_pause == 0:
        return 5  # STOP

    if clean_md_running == 0 \
            and clean_md_selected == 0:
        return 1  # IDLE

    log.error('No cleaning state id could be calculated')
    return None


def _calculate_cleaning_state_id_pna_gco(item, new_tag, new_tag_value, log):
    """
    Calculates the cleaning state ID for PNA GC Ovens based on the current cleaning modes.

    This function updates the item dictionary with a new tag and its integer value, then checks
    the cleaning mode flags (Cooldown Run, CIP Run, Rinse Run, Soak Run) to determine the current
    cleaning state. The system is considered idle if no cleaning modes are active, and in a cleaning
    state if any cleaning mode is active.

    Parameters:
    - item (dict): The original dictionary containing the cleaning mode flags and other information.
    - new_tag (str): The key of the new tag to be added to the item dictionary.
    - new_tag_value: The value of the new tag, which will be converted to an integer.
    - log: A logging object used to log debug information and errors.

    Returns:
    - int: The cleaning state ID (1 for IDLE, 4 for CLEANING) or None if the state cannot be determined.

    The function logs debug messages about the current state and errors if the state cannot be determined.
    """

    new_item = {**item, new_tag: convert_tag_value_to_int(new_tag_value)}
    log.debug(new_item)
    # New logic for PNA GC Ovens
    JBT_Mode_Cooldown_Run = new_item.get(CS_JBT_MODE_COOLDOWN_RUN, False)
    JBT_Mode_CIP_Run = new_item.get(CS_JBT_MODE_CIP_RUN, False)
    JBT_Mode_Rinse_Run = new_item.get(CS_JBT_MODE_RINSE_RUN, False)
    JBT_Mode_Soak_Run = new_item.get(CS_JBT_MODE_SOAK_RUN, False)


    # The system is considered idle if no cleaning modes are currently active
    if not JBT_Mode_Cooldown_Run and not JBT_Mode_CIP_Run:
        log.debug('System is idle, awaiting start of cleaning cycle or in between cycles.')
        return 1  #IDLE

    # If any cleaning mode is active, consider the system to be in a cleaning state
    if JBT_Mode_Cooldown_Run or JBT_Mode_CIP_Run or JBT_Mode_Rinse_Run or JBT_Mode_Soak_Run:
        log.debug('Cleaning process is active.')
        return 4  #CLEANING

    log.error('Unable to determine the GCO cleaning state')

    return None  # This line is a fallback in case none of the conditions above are met



def _calculate_cleaning_state_id_pna_tdo(item, new_tag, new_tag_value, log):
    """
    Calculates the cleaning state ID for PNA TDO based on the current cleaning modes.

    This function updates the item dictionary with a new tag and its integer value, then checks
    the cleaning mode flags (Cooldown Run, CIP Run, Rinse Run, Soak Run) to determine the current
    cleaning state. The system is considered idle if no cleaning modes are active, and in a cleaning
    state if any cleaning mode is active.

    Parameters:
    - item (dict): The original dictionary containing the cleaning mode flags and other information.
    - new_tag (str): The key of the new tag to be added to the item dictionary.
    - new_tag_value: The value of the new tag, which will be converted to an integer.
    - log: A logging object used to log debug information and errors.

    Returns:
    - int: The cleaning state ID (1 for IDLE, 4 for CLEANING) or None if the state cannot be determined.

    The function logs debug messages about the current state and errors if the state cannot be determined.
    """

    new_item = {**item, new_tag: convert_tag_value_to_int(new_tag_value)}
    log.debug(new_item)
    # New logic for PNA TDO
    JBT_Cooldown_Run = new_item.get(CS_JBT_COOLDOWN_RUN, False)
    JBT_CIP_Run = new_item.get(CS_JBT_CIP_RUN, False)
    JBT_Rinse_Run = new_item.get(CS_JBT_RINSE_RUN, False)
    JBT_Soak_Run = new_item.get(CS_JBT_SOAK_RUN, False)


    # The system is considered idle if no cleaning modes are currently active
    if not JBT_Cooldown_Run and not JBT_CIP_Run:
        log.debug('System is idle, awaiting start of cleaning cycle or in between cycles.')
        return 1  #IDLE

    # If any cleaning mode is active, consider the system to be in a cleaning state
    if JBT_Cooldown_Run or JBT_CIP_Run or JBT_Rinse_Run or JBT_Soak_Run:
        log.debug('Cleaning process is active.')
        return 4  #CLEANING

    log.error('Unable to determine the TDO cleaning state')

    return None  # This line is a fallback in case none of the conditions above are met
