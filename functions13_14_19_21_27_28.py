#19
def get_data_item_I048_110(bytes):
    
    binary_octets = bytes.split()
    
    octet1 = binary_octets[0]  
    octet2 = int(binary_octets[1], 2)  #Segundo octeto a entero

    # Ignorar los dos primeros bits del primer octeto y obtener los 14 bits restantes
    height_raw = ((int(octet1, 2) & 0x3FFF) << 8) | octet2  

    if (int(octet1, 2) & 0x20) != 0:  # Si el bit 14 (tercer bit) está activado, es negativo
        height_raw -= (1 << 14)  # Complemento a dos (valor negativo)

    # Convertir la altura a pies (cada unidad = 25 ft)
    height_feet = height_raw * 25

    return height_feet

#21
def get_data_item_I048_230(bytes):

    binary_octets = bytes.split()

    first_octet = binary_octets[0]
    second_octet = binary_octets[1]

    result = {}

    COM = int(first_octet[0:3], 2)  # Bits 16-14
    STAT = int(first_octet[3:6], 2)  # Bits 13-11
    SI = int(first_octet[6], 2)  # Bit 10

    MSSC = int(second_octet[0], 2)  # Bit 8
    ARC = int(second_octet[1], 2)  # Bit 7
    AIC = int(second_octet[2], 2)  # Bit 6
    B1A = (second_octet[3])  # Bit 5
    B1B = (second_octet[4:8])  # Bits 4-1

    if COM == 0:
        result['COM'] = "No communications capability (surveillance only)"
    elif COM == 1:
        result['COM'] = "Comm. A and Comm. B capability"
    elif COM == 2:
        result['COM'] = "Comm. A, Comm. B and Uplink ELM"
    elif COM == 3:
        result['COM'] = "Comm. A, Comm. B, Uplink ELM and Downlink ELM"
    elif COM == 4:
        result['COM'] = "Level 5 Transponder capability"
    else:
        result['COM'] = "Not assigned"

    if STAT == 0:
        result['STAT'] = "No alert, no SPI, aircraft airborne"
    elif STAT == 1:
        result['STAT'] = "No alert, no SPI, aircraft on ground"
    elif STAT == 2:
        result['STAT'] = "Alert, no SPI, aircraft airborne"
    elif STAT == 3:
        result['STAT'] = "Alert, no SPI, aircraft on ground"
    elif STAT == 4:
        result['STAT'] = "Alert, SPI, aircraft airborne or on ground"
    elif STAT == 5:
        result['STAT'] = "No alert, SPI, aircraft airborne or on ground"
    elif STAT == 7:
        result['STAT'] = "Unknown"
    else:
        result['STAT'] = "Not assigned"

    result['SI'] = "II-Code Capable" if SI == 1 else "SI-Code Capable"

    result['MSSC'] = "Yes" if MSSC == 1 else "No"

    result['ARC'] = "25 ft resolution" if ARC == 1 else "100 ft resolution"

    result['AIC'] = "Yes" if AIC == 1 else "No"

    result['B1A'] = "BDS 1,0 bit 16 = " + B1A  

    result['B1B'] = "BDS 1,0 bits 37/40 = " + B1B  

    return result

binary_input = "00100100 11100000" 
p = get_data_item_I048_230(binary_input)
print(p)

