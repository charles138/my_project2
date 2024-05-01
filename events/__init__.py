from sentry_sdk import capture_exception

from jobs.na_to_normalized_mapping.events.alarm_state import is_alarm_tag
from jobs.na_to_normalized_mapping.events.alarm_state import is_ncp_alarm
from jobs.na_to_normalized_mapping.events.alarm_state.calculate import calculate_alarm_events
from jobs.na_to_normalized_mapping.events.alarm_state.calculate_ncp import manage_ncp_alarm
from jobs.na_to_normalized_mapping.events.belt_speed import belt_speed_tags
from jobs.na_to_normalized_mapping.events.belt_speed.calculate import calculate_belt_speed_est
from jobs.na_to_normalized_mapping.events.cleaning_state import cleaning_state_tags
from jobs.na_to_normalized_mapping.events.cleaning_state.calculate import calculate_cleaning_event
from jobs.na_to_normalized_mapping.events.climate_state import climate_system_state_tags
from jobs.na_to_normalized_mapping.events.climate_state.calculate import calculate_climate_system_state_event
from jobs.na_to_normalized_mapping.events.drive_state import drive_state_tags
from jobs.na_to_normalized_mapping.events.drive_state import is_drive_gco
from jobs.na_to_normalized_mapping.events.drive_state.calculate import calculate_drive_event
from jobs.na_to_normalized_mapping.events.drive_state.calculate import calculate_gco_drive_event
from jobs.na_to_normalized_mapping.events.fan_state import is_fan_gco
from jobs.na_to_normalized_mapping.events.fan_state import main_fans_state_tags
from jobs.na_to_normalized_mapping.events.fan_state.calculate import calculate_gco_fan_state_event
from jobs.na_to_normalized_mapping.events.fan_state.calculate import calculate_main_fans_state_event
from jobs.na_to_normalized_mapping.events.production_state import production_state_tags
from jobs.na_to_normalized_mapping.events.production_state.calculate import calculate_production_event


def process_events(events_in, machine_id, container, container_history, log, machine_id_gco, machine_id_tdo):

    try:
        events_out = []
        for event in events_in:
            event = event.asDict()

            events_out.append(event)

            incoming_tag = event.get('id').split('.')[-1]

            # CLEANING STATE
            if incoming_tag in cleaning_state_tags:
                cleaning_event = calculate_cleaning_event(event=event, machine_id=machine_id, container=container, log=log, machine_id_gco=machine_id_gco,machine_id_tdo=machine_id_tdo)

                if cleaning_event:
                    events_out.append(cleaning_event)

            # PRODUCTION STATE
            elif incoming_tag in production_state_tags:
                production_event = calculate_production_event(event=event, machine_id=machine_id, container=container, log=log, machine_id_gco=machine_id_gco,machine_id_tdo=machine_id_tdo)

                if production_event:
                    events_out.append(production_event)

            # ALARM STATE
            elif is_alarm_tag(incoming_tag):
                if is_ncp_alarm(incoming_tag):
                    alarm_events = manage_ncp_alarm(data_frame=event, machine_id=machine_id, container=container, container_history=container_history, log=log)
                else:
                    alarm_events = calculate_alarm_events(event=event, machine_id=machine_id, container=container, log=log)

                if alarm_events:
                    events_out = events_out + alarm_events

            # DRIVE STATE
            elif incoming_tag in drive_state_tags:
                if is_drive_gco(incoming_tag):
                    drive_event = calculate_gco_drive_event(event=event, log=log)
                else:
                    drive_event = calculate_drive_event(event=event, log=log)

                if drive_event:
                    events_out.append(drive_event)

            # CLIMATE_SYSTEM_STATE
            elif incoming_tag in climate_system_state_tags:
                climate_system_state_event = calculate_climate_system_state_event(event=event, log=log)

                if climate_system_state_event:
                    events_out.append(climate_system_state_event)

            # MAIN_FANS_STATE
            elif incoming_tag in main_fans_state_tags:
                if is_fan_gco(incoming_tag):
                    main_fans_state_event = calculate_gco_fan_state_event(event=event, log=log)
                else:
                    main_fans_state_event = calculate_main_fans_state_event(event=event, log=log)

                if main_fans_state_event:
                    events_out.append(main_fans_state_event)

            # BELT SPEED
            elif incoming_tag in belt_speed_tags:
                belt_speed_event = calculate_belt_speed_est(event=event, machine_id=machine_id, container=container, log=log)

                if belt_speed_event:
                    events_out.append(belt_speed_event)

        return events_out
    except Exception as e:
        capture_exception(e)

        raise e
