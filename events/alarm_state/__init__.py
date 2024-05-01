AM_FAULTED_0 = 'Faulted_0'
AM_FAULTED_1 = 'Faulted_1'
AM_FAULTED_2 = 'Faulted_2'
AM_FAULTED_3 = 'Faulted_3'
AM_FAULTED_4 = 'Faulted_4'
AM_FAULTED_5 = 'Faulted_5'
AM_FAULTED_6 = 'Faulted_6'
AM_FAULTED_7 = 'Faulted_7'
AM_FAULTED_8 = 'Faulted_8'
AM_FAULTED_9 = 'Faulted_9'
NCP_ALARM    = 'NCP_Alarm'

alarm_state_tags = [
    AM_FAULTED_0,
    AM_FAULTED_1,
    AM_FAULTED_2,
    AM_FAULTED_3,
    AM_FAULTED_4,
    AM_FAULTED_5,
    AM_FAULTED_6,
    AM_FAULTED_7,
    AM_FAULTED_8,
    AM_FAULTED_9,
]

def is_alarm_tag(tag:str)-> bool:
    if tag in alarm_state_tags:
        return True

    if NCP_ALARM in tag:
        return True
    return False

def is_ncp_alarm(tag:str)-> bool:
    if NCP_ALARM in tag:
        return True
    return False
