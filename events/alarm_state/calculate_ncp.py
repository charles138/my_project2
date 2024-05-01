import datetime
from logging import Logger

from azure.cosmos.container import ContainerProxy

from app.utils import alarm as alarm_utility


def deactivate_alarm(
    machine_id:str, alarm_tag:str, alarm_item:dict,
    alarm_container:ContainerProxy, container_history:ContainerProxy, alarm_tag_timestamp, log: Logger,
):
    record_creation_date = alarm_utility.date_time_to_iso_format(datetime.datetime.utcnow())

    try:
        original_active_alarms = alarm_item['active_alarms'][alarm_tag]
        del alarm_item['active_alarms'][alarm_tag]
    except KeyError:
        original_active_alarms = []

    active_alarms = alarm_item['active_alarms']
    alarm_item['last_updated'] = record_creation_date
    alarm_item['active_alarms'] = active_alarms
    # Update active alarms
    alarm_item = alarm_utility.create_or_upsert(container=alarm_container, item=alarm_item)
    alarm_utility.build_alarm_history(
        machine_id, alarm_tag, 0, original_active_alarms, [],
        container_history, alarm_tag_timestamp, log,
    )
    log.debug(f'Deactivated {alarm_tag} for machine:{machine_id}.')


def activate_alarm(
    active_alarms:list, alarm_item:dict, alarm_tag:str, alarm_tag_value_number:int,
    alarm_container:ContainerProxy, container_history:ContainerProxy, alarm_tag_timestamp, log: Logger,
)-> dict:
    try:
        original_active_alarms = alarm_item['active_alarms'][alarm_tag]
    except KeyError:
        original_active_alarms = []
    log.debug(f'Original active alarms: {original_active_alarms}.')
    record_creation_date = alarm_utility.date_time_to_iso_format(datetime.datetime.utcnow())
    alarm_tag_datetime = datetime.datetime.fromtimestamp(int(alarm_tag_timestamp[:10])).isoformat()+ '+00:00'
    active_alarm_attributes:list = []

    for alarm in active_alarms:
        active_alarm: dict = {}
        alarm_number = int(alarm)
        # Update the latest Alarm status
        active_alarm['alarm_code'] = alarm_number

        if len(alarm_item['active_alarms']) > 0:
            #If an alarm has already been triggerred, don't update the last updated field so we know how long this alarm has been active
            last_updated = alarm_utility.get_last_updated(alarm_item['active_alarms'], alarm_tag, active_alarm['alarm_code'])
            if last_updated:
                active_alarm['last_updated'] = last_updated
            else:
                active_alarm['last_updated'] = alarm_tag_datetime
        else:
            active_alarm['last_updated'] = alarm_tag_datetime
        active_alarm_attributes.append(active_alarm)

    alarm_item['last_updated'] = record_creation_date
    alarm_item['active_alarms'][alarm_tag] = active_alarm_attributes
    log.debug(f'Active alarms attributes: {active_alarm_attributes} alarm items: {alarm_item}.')
    alarm_item = alarm_utility.create_or_upsert(container=alarm_container, item=alarm_item)
    alarm_utility.build_alarm_history(
        alarm_item['machine_id'], alarm_tag, alarm_tag_value_number,
        original_active_alarms, active_alarm_attributes, container_history,
        alarm_tag_timestamp, log,
    )
    log.debug(f'Activated {alarm_tag} for machine {alarm_item["machine_id"]}. Activated alarm codes {active_alarms}.')


def manage_ncp_alarm(data_frame:dict, machine_id:str, container:ContainerProxy, container_history:ContainerProxy, log: Logger)-> list:
    return_events = []
    alarm_tag = data_frame.get('id').split('.')[-1]
    alarm_tag_value = data_frame.get('v')
    alarm_tag_timestamp = data_frame.get('t')
    alarm_item = alarm_utility.return_alarm_item(machine_id, container, alarm_tag_timestamp)
    alarm_tag_value_number = alarm_utility.convert_to_number(alarm_tag_value)
    log.debug(f'Alarm items {alarm_item} for machine:{machine_id} and data frame:{data_frame}.')
    if alarm_tag_value_number == 0:
        deactivate_alarm(machine_id, alarm_tag, alarm_item, container,container_history, alarm_tag_timestamp, log)
        return_events.append({
        'id': 0,
        'v': 0,
        't': alarm_tag_timestamp,
        })
        return return_events
    else:
        try:
            # Find out all the alarm codes associatted with the alarm tag and alarm_tag_value_number
            active_alarms = alarm_utility.get_active_alarm_codes(8, alarm_tag, alarm_tag_value_number, log)
        except ValueError:
            message = f'Machine ({machine_id}) provided an incorrect alarm value for {alarm_tag}={alarm_tag_value}.'
            log.warning(message)
            return return_events
        except KeyError:
            message = f'Machine ({machine_id}) provided an unexpected tag format value/name {alarm_tag}.'
            log.critical(message)
            return return_events
        log.debug(f'Active alarms: {active_alarms}.')
        activate_alarm(
            active_alarms, alarm_item, alarm_tag, alarm_tag_value_number, container,
            container_history, alarm_tag_timestamp, log,
        )

        for index, alarm in enumerate(active_alarms):
            return_events.append({
            'id': index,
            'v': alarm,
            't': alarm_tag_timestamp,
            })
        return return_events
