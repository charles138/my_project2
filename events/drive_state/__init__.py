DS_BELT_STATUS_IND = 'BeltStatusInd'
DS_JBT_BELT_SPEED = 'JBT_BELT_CONTROL_BELT_SPEED_ACTUAL'
DS_JBT_CNV='MainConveyorRunning'

drive_state_tags = [
    DS_BELT_STATUS_IND,
    DS_JBT_BELT_SPEED,
    DS_JBT_CNV,
]
def is_drive_gco(tag:str)-> bool:
    if DS_JBT_CNV in tag:
        return True
    return False
