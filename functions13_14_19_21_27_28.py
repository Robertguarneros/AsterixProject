#13
def get_data_item_I048_200(bytes):

    binary_octets = bytes.split()

    data = [int(octet, 2) for octet in binary_octets]

    groundspeed_raw = (data[0] << 8) + data[1]  # Combina octeto 1 y octeto 2

    heading_raw = (data[2] << 8) + data[3]  # Combina octeto 3 y octeto 4

    # El LSB es 2^-14 NM/s, 0.22 nudos por bit
    groundspeed = groundspeed_raw * (2 ** -14) * 3600  # Convertir de NM/s a nudos (1 NM/s = 3600 NM/h = 3600 knots)

    # El LSB es 360° / 2^16, 0.0055 grados por bit
    heading = heading_raw * (360 / 65536)  # 2^16 = 65536

    print(groundspeed)
    print(heading)

    return groundspeed, heading


binary_input = "00000111 01000010 10111001 01100010"
get_data_item_I048_200(binary_input)


#14
def get_data_item_I048_170(bytes):

    binary_octets = bytes.split()

    result = {}

    first_octet = binary_octets[0]

    CNF = int(first_octet[0]) 
    RAD = int(first_octet[1:3], 2)  # Bits 7/6
    DOU = int(first_octet[3])  # Bit 5
    MAH = int(first_octet[4])  # Bit 4
    CDM = int(first_octet[5:7], 2)  # Bits 3/2
    FX = int(first_octet[7])  # Bit 1 (LSB)

    result['CNF'] = "Tentative Track" if CNF == 1 else "Confirmed Track"
    if RAD == 0:
        result['RAD'] = "Combined Track"
    elif RAD == 1:
        result['RAD'] = "PSR Track"
    elif RAD == 2:
        result['RAD'] = "SSR/Mode S Track"
    else:
        result['RAD'] = "Invalid"

    result['DOU'] = "Low confidence" if DOU == 1 else "Normal confidence"
    result['MAH'] = "Horizontal maneuver sensed" if MAH == 1 else "No horizontal maneuver sensed"

    if CDM == 0:
        result['CDM'] = "Maintaining"
    elif CDM == 1:
        result['CDM'] = "Climbing"
    elif CDM == 2:
        result['CDM'] = "Descending"
    else:
        result['CDM'] = "Unknown"

    used_octets = 1

    if FX == 1:
        result['TRE'] = []
        result['GHO'] = []
        result['SUP'] = []
        result['TCC'] = []
        i = 1
        while i<len(binary_octets):
            current_octet = binary_octets[i]

            TRE = int(current_octet[0]) 
            GHO = int(current_octet[1]) 
            SUP = int(current_octet[2])  
            TCC = int(current_octet[3])  
            FX = int(current_octet[7]) 

            result['TRE'].append("End of track" if TRE == 1 else "Track still alive")
            result['GHO'].append("Ghost target" if GHO == 1 else "True target")
            result['SUP'].append("Track maintained by neighboring node" if SUP == 1 else "No neighboring node")
            result['TCC'].append("Slant range correction" if TCC == 1 else "Radar plane tracking")
          
            used_octets += 1

            if FX == 0:
                break
            else:
                i += 1
        
    remaining_octets = binary_octets[used_octets:]

                
    return result, remaining_octets

# Example usage
binary_input = "11000001 10000001 00110000 01011111" 
result = get_data_item_I048_170(binary_input)
print(result)


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


binary_input = "00100000 00001010"  
t = get_data_item_I048_110(binary_input)
print(t)


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

