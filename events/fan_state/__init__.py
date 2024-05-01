MF_EVAP_FAN_STATUS = 'EvapFanStatus'
MF_JBT_Circ1 = 'CirculationFanDriveRunning'

main_fans_state_tags = [
    MF_EVAP_FAN_STATUS,
    MF_JBT_Circ1,
]

def is_fan_gco(tag:str)-> bool:
    if MF_JBT_Circ1 in tag:
        return True
    return False
