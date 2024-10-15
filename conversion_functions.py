import re

# Open and read binary
def read_and_split_binary(input_file):
    lines = []  # List to store the output lines
    try:
        # Open the binary file
        with open(input_file, "rb") as binary_file:
            while True:
                # Read 1 octet for CAT (the category)
                cat = binary_file.read(1)
                if not cat:
                    break  # End of file
                
                # Convert the CAT byte to its binary representation
                cat_binary = format(ord(cat), "08b")

                # Read 2 octets for Length
                length_octet_1 = binary_file.read(1)
                length_octet_2 = binary_file.read(1)
                
                if not length_octet_1 or not length_octet_2:
                    break  # End of file or incomplete data

                # Convert length octets to binary
                length_binary_1 = format(ord(length_octet_1), "08b")
                length_binary_2 = format(ord(length_octet_2), "08b")
                
                # Combine both length octets and convert to an integer
                length = int(length_binary_1 + length_binary_2, 2)

                # Calculate the remaining length (excluding CAT and length fields)
                remaining_length = length - 3  # 1 octet CAT + 2 octets Length

                # Create a new line with CAT, Length, and the remaining octets
                new_line = cat_binary + " " + length_binary_1 + " " + length_binary_2 + " "

                # Read the remaining octets based on the length and add to the line
                for _ in range(remaining_length):
                    byte = binary_file.read(1)
                    if not byte:
                        break  # End of file or incomplete data
                    byte_binary = format(ord(byte), "08b")
                    new_line += byte_binary + " "

                # Add the complete line to the list
                lines.append(new_line.strip())

    except FileNotFoundError:
        print(f"File {input_file} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return lines  # Return the list of lines

# Get fspec for each line
def get_fspec(line):
    DataItems = []
    unused_octets = []  # List to store unused/unread octets
    separated_line = re.split(r"\s+", line.strip())

    # Remove the first 3 elements (as per your current logic)
    del separated_line[0:3]
    
    fspec = ""
    
    for i, octet in enumerate(separated_line):
        fspec += octet + " "

        # If the last bit is 0, FSPEC ends, and we stop reading
        if octet[7] == "0":
            unused_octets = separated_line[i + 1:]  # Store remaining unread octets
            break
    
    # Remove spaces in FSPEC string
    fspec = fspec.replace(" ", "")
    
    # Parse the FSPEC bits
    for i, bit in enumerate(fspec):
        if i in {6, 15, 23, 31}:
            # Skip specific positions (as per your current logic)
            pass
        else:
            # Append True for '1' and False for '0'
            if bit == "1":
                DataItems.append(True)
            elif bit == "0":
                DataItems.append(False)

    return DataItems, unused_octets

# Decode 010
def get_sac_sic(message):
        
    # Dividimos el mensaje en tres octetos
    first_octet = message.split()[0]  
    second_octet = message.split()[1]  

    # Convertimos los binarios a enteros
    sac = int(first_octet, 2)  # SAC (System Area Code) en binario a decimal
    sic = int(second_octet, 2)  # SIC (System Identification Code) en binario a decimal
        
    # Retornamos los valores de SAC y SIC descodificados
    return sac, sic

# Decode 140
def get_time_of_day(message):

    # Dividimos el mensaje en tres octetos
    first_octet = message.split()[0]  
    second_octet = message.split()[1]  
    third_octet = message.split()[2]  

    # Concatenamos los tres octetos para obtener el valor en binario de 24 bits
    time_of_day_bin = first_octet + second_octet + third_octet

    # Convertimos el binario a decimal
    time_of_day = int(time_of_day_bin, 2)

    # Convertimos de unidades de 1/128 segundos a segundos reales
    total_seconds = time_of_day / 128

    # Calculamos horas, minutos y segundos
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = total_seconds % 60

    time = f'{hours:02}:{minutes:02}:{seconds:06.3f}'

    # Retornamos los valores calculados
    return time, total_seconds

# Decode 020
def get_target_report_descriptor(message):
    # Initialize all values
    TYP = SIM = RDP = SPI = RAB = TST = ERR = XPP = ME = MI = FOE_FRI = ADSB_EP = ADSB_VAL = SCN_EP = SCN_VAL = PAI_EP = PAI_VAL = None

    # Split the message into octets
    octets = message
    unused_octets = octets.copy()  # Make a copy to track unused octets

    if not octets:
        return None, unused_octets  # Return if there are no octets to decode

    # Decode the first octet
    first_octet = octets[0]
    unused_octets.pop(0)  # Remove the first octet from unused_octets

    # Extract bits from the first octet
    typ = first_octet[:3]  # Bits 8/6 (TYP)
    sim = first_octet[3]   # Bit 5 (SIM)
    rdp = first_octet[4]   # Bit 4 (RDP)
    spi = first_octet[5]   # Bit 3 (SPI)
    rab = first_octet[6]   # Bit 2 (RAB)
    FX1 = first_octet[7]   # Bit 1 (FX of first octet)

    # Interpret the values of TYP
    typ_meaning = {
        '000': "No detection",
        '001': "Single PSR detection",
        '010': "Single SSR detection",
        '011': "SSR + PSR detection",
        '100': "Single ModeS All-Call",
        '101': "Single ModeS Roll-Call",
        '110': "ModeS All-Call + PSR",
        '111': "ModeS Roll-Call + PSR"
    }

    # Save results of the first octet
    TYP = typ_meaning.get(typ, "Unknown Detection Type")  # Detection type
    SIM = 'Simulated target report' if sim == '1' else 'Actual target report'  # Target report
    RDP = 'RDP Chain 2' if rdp == '1' else 'RDP Chain 1'  # Report from RDP
    SPI = 'Presence of SPI' if spi == '1' else 'Absence of SPI'  # Special Position Identification
    RAB = 'Report from field monitor (fixed transponder)' if rab == '1' else 'Report from aircraft transponder'

    # If FX1 is 1, we need to decode the second octet
    if FX1 == '1' and len(unused_octets) > 0:
        second_octet = octets[1]
        unused_octets.pop(0)  # Remove the second octet from unused_octets

        # Decode the second octet
        tst = second_octet[0]  # Bit 8 (TST)
        err = second_octet[1]  # Bit 7 (ERR)
        xpp = second_octet[2]  # Bit 6 (XPP)
        me = second_octet[3]   # Bit 5 (ME)
        mi = second_octet[4]   # Bit 4 (MI)
        foe_fri = second_octet[5:7]  # Bits 3/2 (FOE/FRI)
        FX2 = second_octet[7]  # Bit 1 (FX of second octet)

        # Interpret FOE/FRI
        foe_fri_meaning = {
            '00': "No Mode 4 interrogation",
            '01': "Friendly target",
            '10': "Unknown target",
            '11': "No reply"
        }

        # Save results of the second octet
        TST = 'Test target report' if tst == '1' else 'Real target report'
        ERR = 'Extended Range present' if err == '1' else 'No Extended Range'
        XPP = 'X-Pulse present' if xpp == '1' else 'No X-Pulse present'
        ME = 'Military emergency' if me == '1' else 'No military emergency'
        MI = 'Military identification' if mi == '1' else 'No military identification'
        FOE_FRI = foe_fri_meaning.get(foe_fri, "Error decoding FOE/FRI")

        # If FX2 is 1, we need to decode the third octet
        if FX2 == '1' and len(unused_octets) > 0:
            third_octet = octets[2]
            unused_octets.pop(0)  # Remove the third octet from unused_octets

            # Decode the third octet
            adsb_ep = third_octet[0]  # Bit 8 (ADSB#EP)
            adsb_val = third_octet[1]  # Bit 7 (ADSB#VAL)
            scn_ep = third_octet[2]    # Bit 6 (SCN#EP)
            scn_val = third_octet[3]   # Bit 5 (SCN#VAL)
            pai_ep = third_octet[4]    # Bit 4 (PAI#EP)
            pai_val = third_octet[5]   # Bit 3 (PAI#VAL)
            FX3 = third_octet[7]       # Bit 2 (FX of third octet)

            # Save results of the third octet
            ADSB_EP = 'ADSB populated' if adsb_ep == '1' else 'ADSB not populated'
            ADSB_VAL = 'Available' if adsb_val == '1' else 'Not Available'
            SCN_EP = 'SCN populated' if scn_ep == '1' else 'SCN not populated'
            SCN_VAL = 'Available' if scn_val == '1' else 'Not Available'
            PAI_EP = 'PAI populated' if pai_ep == '1' else 'PAI not populated'
            PAI_VAL = 'Available' if pai_val == '1' else 'Not Available'

    # Return all decoded fields and the remaining unused octets
    return TYP, SIM, RDP, SPI, RAB, TST, ERR, XPP, ME, MI, FOE_FRI, ADSB_EP, ADSB_VAL, SCN_EP, SCN_VAL, PAI_EP, PAI_VAL, unused_octets

# Decode 040 
def get_measured_position_in_slant_coordinates(message):

    # Dividimos el mensaje en cuatro octetos (0,1 = RHO; 2,3 = THETA)
    first_octet = message.split()[0]  
    second_octet = message.split()[1]  
    third_octet = message.split()[2]  
    fourth_octet = message.split()[3]  

    # Concatenamos los primeros dos octetos para obtener el valor de RHO (16 bits)
    rho_bin = first_octet + second_octet
    # Concatenamos los últimos dos octetos para obtener el valor de THETA (16 bits)
    theta_bin = third_octet + fourth_octet

    # Convertimos los binarios a decimal
    RHO = int(rho_bin, 2) * (1 / 256)  # RHO en NM (cada bit es 1/256 NM)
    THETA = int(theta_bin, 2) * (360 / 65536)  # THETA en grados (216 = 65536)

    # Retornamos los valores de RHO y THETA
    return RHO, THETA

# Decode 070
def get_mode3a_code(message):

     # Dividimos el mensaje en dos octetos
    first_octet_bin = message.split()[0] 
    second_octet_bin = message.split()[1] 

    # Extraemos los bits de control directamente
    V = 'Code not validated' if first_octet_bin[0] == '1' else 'Code Validated'  # Bit 16: Validación (V)
    G = 'Garbled code' if first_octet_bin[1] == '1' else 'Default'  # Bit 15: Código Garbled (G)
    L = 'Mode-3/A code not extracted during the last scan' if first_octet_bin[2] == '1' else 'Mode-3/A code derived from the reply of the transponder'  # Bit 14: Código derivado en la última exploración (L)

    # Extraemos el código Mode-3/A en formato octal de bits 12 a 1 (de A4 a D1)
    A = (int(first_octet_bin[4]) * 4) + (int(first_octet_bin[5]) * 2) + int(first_octet_bin[6])
    B = (int(first_octet_bin[7]) * 4) + (int(second_octet_bin[0]) * 2) + int(second_octet_bin[1])
    C = (int(second_octet_bin[2]) * 4) + (int(second_octet_bin[3]) * 2) + int(second_octet_bin[4])
    D = (int(second_octet_bin[5]) * 4) + (int(second_octet_bin[6]) * 2) + int(second_octet_bin[7])

    # Convertimos el código Mode-3/A en una representación octal
    mode_3a_code = f'{A}{B}{C}{D}'

    # Retornamos los valores de los bits de control y el código octal
    return V, G, L, mode_3a_code

# Decode 090
def get_flight_level(message):

    # Dividimos el mensaje en dos octetos
    first_octet_bin = message.split()[0]  # Primer octeto en binario
    second_octet_bin = message.split()[1]  # Segundo octeto en binario

    # Extraemos los bits de control directamente
    V = 'Code not validated' if first_octet_bin[0] == '1' else 'Code Validated'  # Bit 16: Validación (V)
    G = 'Garbled code' if first_octet_bin[1] == '1' else 'Default'  # Bit 15: Código Garbled (G)

    # Extraemos el nivel de vuelo (bits 14 a 1) como un solo bloque
    flight_level_bin = first_octet_bin[2:] + second_octet_bin  # De bits 14 a 1

    # Convertimos el nivel de vuelo a decimal
    flight_level = int(flight_level_bin, 2) * 0.25  # LSB=1/4 FL

    # Retornamos los valores de los bits de control y el nivel de vuelo
    return V, G, flight_level

# Decode 130
def get_radar_plot_characteristics(octet_list):
    # Ensure the list has at least one octet
    if len(octet_list) < 1:
        raise ValueError("Input must be at least 1 octet long")

    # Get the primary subfield (first octet)
    primary_subfield = octet_list[0]

    # Check which subfields are present
    subfields = {
        "SRL": primary_subfield[0] == '1',  # Subfield #1 SSR Plot Runlength
        "SRR": primary_subfield[1] == '1',  # Subfield #2 Number of received replies for MSSR
        "SAM": primary_subfield[2] == '1',  # Subfield #3 Amplitude of MSSR reply
        "PRL": primary_subfield[3] == '1',  # Subfield #4 PSR Plot Runlength
        "PAM": primary_subfield[4] == '1',  # Subfield #5 Amplitude of PSR Plot
        "RPD": primary_subfield[5] == '1',  # Subfield #6 Difference in range (PSR-SSR)
        "APD": primary_subfield[6] == '1',  # Subfield #7 Difference in azimuth (PSR-SSR)
        "FX": primary_subfield[7] == '1',   # Extension into next octet
    }
    
    # Initialize results dictionary
    result = {}

    # Start processing octets after the primary subfield
    octet_index = 1

    # Subfield #1 (SSR Plot Runlength)
    if subfields["SRL"] and octet_index < len(octet_list):
        srl_bits = octet_list[octet_index]
        srl_value = int(srl_bits, 2) * (360 / 2**13)
        result["SSR Plot Runlength (degrees)"] = str(srl_value) + "dg"
        octet_index += 1
    else:
        result["SSR Plot Runlength (degrees)"] = "N/A"

    
    # Subfield #2 (Number of received replies for MSSR)
    if subfields["SRR"] and octet_index < len(octet_list):
        srr_bits = octet_list[octet_index]
        srr_value = int(srr_bits, 2)  # LSB = 1
        result["Number of received replies for MSSR"] = str(srr_value)
        octet_index += 1
    else:
        result["Number of received replies for MSSR"] = "N/A"

    
    # Subfield #3 (Amplitude of MSSR Reply)
    if subfields["SAM"] and octet_index < len(octet_list):
        sam_bits = octet_list[octet_index]
        sam_value = int(sam_bits, 2) if sam_bits[0] == '0' else int(sam_bits, 2) - (1 << 8)
        result["Amplitude of MSSR Reply (dBm)"] = str(sam_value) + "dBm"
        octet_index += 1
    else:
        result["Amplitude of MSSR Reply (dBm)"] = "N/A"
    
    # Subfield #4 (Primary Plot Runlength)
    if subfields["PRL"] and octet_index < len(octet_list):
        prl_bits = octet_list[octet_index]
        prl_value = int(prl_bits, 2) * (360 / 2**13)
        result["Primary Plot Runlength (degrees)"] = str(prl_value) + "dg"
        octet_index += 1
    else:
        result["Primary Plot Runlength (degrees)"] = "N/A"

    
    # Subfield #5 (Amplitude of Primary Plot)
    if subfields["PAM"] and octet_index < len(octet_list):
        pam_bits = octet_list[octet_index]
        pam_value = int(pam_bits, 2) if pam_bits[0] == '0' else int(pam_bits, 2) - (1 << 8)
        result["Amplitude of Primary Plot (dBm)"] = str(pam_value) + "dBm"
        octet_index += 1
    else:
        result["Amplitude of Primary Plot (dBm)"] = "N/A"
    
    # Subfield #6 (Difference in Range between PSR and SSR plot)
    if subfields["RPD"] and octet_index < len(octet_list):
        rpd_bits = octet_list[octet_index]
        rpd_value = int(rpd_bits, 2) if rpd_bits[0] == '0' else int(rpd_bits, 2) - (1 << 8)
        result["Difference in Range (PSR-SSR) (NM)"] = str(rpd_value / 256) + "NM"
        octet_index += 1
    else:
        result["Difference in Range (PSR-SSR) (NM)"] = "N/A"

    
    # Subfield #7 (Difference in Azimuth between PSR and SSR plot)
    if subfields["APD"] and octet_index < len(octet_list):
        apd_bits = octet_list[octet_index]
        apd_value = int(apd_bits, 2) if apd_bits[0] == '0' else int(apd_bits, 2) - (1 << 8)
        result["Difference in Azimuth (PSR-SSR) (degrees)"] = str(apd_value * (360 / 2**14)) + "dg"
        octet_index += 1
    else:
        result["Difference in Azimuth (PSR-SSR) (degrees)"] = "N/A"


    # Return the result and any remaining octets
    remaining_octets = octet_list[octet_index:]  # Get remaining octets
    return result, remaining_octets  # Return result and unused octets as a list

# Decode 220
def get_aircraft_address(bytes):
    # Data Item I048/220
    bytes = bytes.replace(" ", "")

    # Convert binary string to an integer using base 2
    integer_value = int(bytes, 2)

    # Convert the integer to a hexadecimal string
    hex_value = hex(integer_value)[2:].upper()

    return hex_value

# Mapping 6-bit binary to characters (ICAO 6-bit encoding for ASTERIX)
six_bit_to_char = {
    '000001': 'A', '000010': 'B', '000011': 'C', '000100': 'D', '000101': 'E',
    '000110': 'F', '000111': 'G', '001000': 'H', '001001': 'I', '001010': 'J',
    '001011': 'K', '001100': 'L', '001101': 'M', '001110': 'N', '001111': 'O',
    '010000': 'P', '010001': 'Q', '010010': 'R', '010011': 'S', '010100': 'T',
    '010101': 'U', '010110': 'V', '010111': 'W', '011000': 'X', '011001': 'Y',
    '011010': 'Z', '110000': '0', '110001': '1', '110002': '2', '110011': '3',
    '110100': '4', '110101': '5', '110110': '6', '110111': '7', '111000': '8',
    '111001': '9', '100000': ' ',  # Space
}

# Decode 240
def get_aircraft_identification(bytes_str):
    # Remove spaces from the input string
    bytes_str = bytes_str.replace(" ", "")
    
    # Iterate over the binary string in 6-bit chunks
    ascii_result = ''
    for i in range(0, len(bytes_str), 6):
        byte = bytes_str[i:i+6]
        
        # Convert the 6-bit binary to a character using the dictionary
        if byte in six_bit_to_char:
            ascii_result += six_bit_to_char[byte]
        else:
            ascii_result += '?'  # Handle any invalid 6-bit chunks
        ascii_result = ascii_result.replace(" ", "")
    return ascii_result

# Decode 250
def get_mode_s_mb_data(octet_list):
    if len(octet_list) < 1:
        raise ValueError("Input list must contain at least 1 octet")

    # First octet is the REP field
    REPField = int(octet_list[0], 2)

    BDSItems = []
    remaining_octets = octet_list[1:]  # Remove REP field

    # Extract BDS items (each item is 64 bits or 8 octets)
    for i in range(REPField):
        if len(remaining_octets) < 8:
            raise ValueError("Not enough octets for expected BDS items")

        BDSItems.append(remaining_octets[:8])
        remaining_octets = remaining_octets[8:]  # Remove used octets

    ModesPresent = []
    
    # Default all values to "N/A" for BDS 4.0, 5.0, and 6.0
    resultBDS4 = {
        "MCP/FCU SELECTED ALTITUDE": "N/A",
        "FMS SELECTED ALTITUDE": "N/A",
        "BAROMETRIC PRESSURE SETTING": "N/A",
        "VNAV MODE": "N/A",
        "ALT HOLD MODE": "N/A",
        "APPROACH MODE": "N/A",
        "TARGET ALT SOURCE": "N/A"
    }

    resultBDS5 = {
        "Roll Angle": "N/A",
        "True Track Angle": "N/A",
        "Ground Speed": "N/A",
        "Track Angle Rate": "N/A",
        "True Airspeed": "N/A"
    }

    resultBDS6 = {
        "MAGNETIC HEADING": "N/A",
        "Indicated Airspeed": "N/A",
        "Mach Number": "N/A",
        "Barometric Altitude Rate": "N/A",
        "Inertial Vertical Speed": "N/A"
    }

    # Process each BDS item
    for item in BDSItems:
        # Combine 8 octets into one bit string for easier bit manipulation
        item_bits = ''.join(item)
        
        BDS1 = int(item_bits[56:60], 2)
        BDS2 = int(item_bits[60:64], 2)
        BDSTotal = f"{BDS1},{BDS2}"
        ModesPresent.append("BDS:" + BDSTotal)

        if BDSTotal == "4,0":
            # Populate only the required values from BDS 4.0
            resultBDS4["MCP/FCU SELECTED ALTITUDE"] = int(item_bits[1:13], 2) * 16
            resultBDS4["FMS SELECTED ALTITUDE"] = int(item_bits[14:26], 2) * 16
            resultBDS4["BAROMETRIC PRESSURE SETTING"] = int(item_bits[27:39], 2) * 0.1 + 800
            resultBDS4["VNAV MODE"] = "Active" if item_bits[49:50] == "1" else "Not Active"
            resultBDS4["ALT HOLD MODE"] = "Active" if item_bits[50:51] == "1" else "Not Active"
            resultBDS4["APPROACH MODE"] = "Active" if item_bits[51:52] == "1" else "Not Active"
            target_alt_source_mapping = {
                "00": "Unknown",
                "01": "Aircraft Altitude",
                "10": "FCU/MCP Selected Altitude",
                "11": "FMS Selected Altitude"
            }
            resultBDS4["TARGET ALT SOURCE"] = target_alt_source_mapping.get(item_bits[54:56], "Unknown")

        elif BDSTotal == "5,0":
            # Populate only the required values from BDS 5.0
            roll_angle = int(item_bits[1:11], 2)
            if roll_angle >= 2**9:
                roll_angle -= 2**10
            resultBDS5["Roll Angle"] = roll_angle * (45 / 256)
            
            true_track_angle = int(item_bits[12:23], 2)
            if true_track_angle >= 2**10:
                true_track_angle -= 2**11
            resultBDS5["True Track Angle"] = true_track_angle * (90 / 512)
            
            ground_speed = int(item_bits[25:34], 2)
            resultBDS5["Ground Speed"] = ground_speed * (1024 / 512)
            
            track_angle_rate = int(item_bits[35:45], 2)
            if track_angle_rate >= 2**9:
                track_angle_rate -= 2**10
            resultBDS5["Track Angle Rate"] = track_angle_rate * (8 / 256)
            
            true_airspeed = int(item_bits[47:56], 2)
            resultBDS5["True Airspeed"] = true_airspeed * 2

        elif BDSTotal == "6,0":
            # Populate only the required values from BDS 6.0
            magnetic_heading = int(item_bits[1:12], 2)
            if magnetic_heading >= 2**10:
                magnetic_heading -= 2**11
            resultBDS6["MAGNETIC HEADING"] = magnetic_heading * (90 / 512)
            
            indicated_airspeed = int(item_bits[13:23], 2)
            resultBDS6["Indicated Airspeed"] = indicated_airspeed
            
            mach_number = int(item_bits[24:34], 2)
            resultBDS6["Mach Number"] = mach_number * (2.048 / 512)
            
            barometric_altitude_rate = int(item_bits[35:45], 2)
            if barometric_altitude_rate >= 2**9:
                barometric_altitude_rate -= 2**10
            resultBDS6["Barometric Altitude Rate"] = barometric_altitude_rate * (8192 / 256)
            
            inertial_vertical_speed = int(item_bits[46:56], 2)
            if inertial_vertical_speed >= 2**9:
                inertial_vertical_speed -= 2**10
            resultBDS6["Inertial Vertical Speed"] = inertial_vertical_speed * (8192 / 256)

    # Return the relevant results and the remaining octets
    return ModesPresent, resultBDS4, resultBDS5, resultBDS6, remaining_octets

# Decode 161
def get_track_number(bytes):
    # Data Item I048/161
    bytes = bytes.replace(" ", "")

    # Convert binary string to an integer using base 2
    integer_value = int(bytes, 2)

    return integer_value

# Decode 042
def get_calculated_position(bytes):
    # Remove spaces from input
    bytes = bytes.replace(" ", "")
    
    # Split the byte_string into the X and Y components
    # The first two octets represent the X-component
    # The second two octets represent the Y-component
    x_bin = bytes[:16]  # First two octets (16 bits)
    y_bin = bytes[16:]  # Second two octets (16 bits)
    
    # Convert the X and Y binary strings from two's complement to integer
    x_int = int(x_bin, 2) if x_bin[0] == '0' else int(x_bin, 2) - (1 << 16)
    y_int = int(y_bin, 2) if y_bin[0] == '0' else int(y_bin, 2) - (1 << 16)
    
    # The LSB is 1/128 NM, so divide by 128 to get the final value in NM
    x_nm = x_int / 128.0
    y_nm = y_int / 128.0
    
    return x_nm, y_nm

def convert_to_csv(input_file):
    lines = read_and_split_binary(input_file)
    csv_lines = []
    new_csv_line = "NUM;SAC;SIC;TIME;TIME(s);LAT;LON;H;TYP_020;SIM_020;RDP_020;SPI_020;RAB_020;TST_020;ERR_020;XPP_020;ME_020;MI_020;FOE_FRI_020;RHO;THETA;V_070;G_070;MODE 3/A;V_090;G_090;FL;MODE C corrected;SRL_130;SSR_130;SAM_130;PRL_130;PAM_130;RPD_130;APD_130;TA;TI;MCP_ALT;FMS_ALT;BP;VNAV;ALT_HOLD;APP;TARGET_ALT_SOURCE;RA;TTA;GS;TAR;TAS;HDG;IAS;MACH;BAR;IVV;TN;X;Y;GS_KT;HEADING;CNF_170;RAD_170;DOU_170;MAH_170;CDM_170;TRE_170;GHO_170;SUP_170;TCC_170;HEIGHT;COM_230;STAT_230;SI_230;MSCC_230;ARC_230;AIC_230;B1A_230;B1B_230"
    csv_lines.append(new_csv_line)
    i=1
    for line in lines:
        new_csv_line = str(i)+";"
        fspec, remaining_line = get_fspec(line)
    # 1 Data Item 010 SAC, SIC
        if fspec[0] == True:
            message = remaining_line.pop(0)+" "+remaining_line.pop(0)
            sac, sic = get_sac_sic(message)
            new_csv_line = new_csv_line+str(sac)+";"+str(sic)+";"
        elif fspec[0] == False:
            sac = sic = "N/A"
            new_csv_line = new_csv_line+str(sac)+";"+str(sic)+";"
    # 2 Data Item 140 Time of Day
        if fspec[1] == True:
            message = remaining_line.pop(0)+" "+remaining_line.pop(0)+" "+remaining_line.pop(0)
            time, total_seconds = get_time_of_day(message)
            new_csv_line = new_csv_line+str(time)+";"+str(total_seconds)+";"
        elif fspec[1] == False:
            time = total_seconds = "N/A"
            new_csv_line = new_csv_line+str(time)+";"+str(total_seconds)+";"
    # 3 Data Item 020 Target Report Descriptor
        if fspec[2] == True:
            message = remaining_line
            TYP, SIM, RDP, SPI, RAB, TST, ERR, XPP, ME, MI, FOE_FRI, ADSB_EP, ADSB_VAL, SCN_EP, SCN_VAL, PAI_EP, PAI_VAL, remaining_line_040 = get_target_report_descriptor(message)
            new_csv_line = new_csv_line +";"+ str(TYP)+";"+str(SIM)+";"+str(RDP)+";"+str(SPI)+";"+str(RAB)+";"+str(TST)+";"+str(ERR)+";"+str(XPP)+";"+str(ME)+";"+str(MI)+";"+str(FOE_FRI)
            remaining_line = remaining_line_040
        elif fspec[2] == False:
            TYP = SIM = RDP = SPI = RAB = TST = ERR = XPP = ME = MI = FOE_FRI = "N/A"
            new_csv_line = new_csv_line +";"+ str(TYP)+";"+str(SIM)+";"+str(RDP)+";"+str(SPI)+";"+str(RAB)+";"+str(TST)+";"+str(ERR)+";"+str(XPP)+";"+str(ME)+";"+str(MI)+";"+str(FOE_FRI)
    # 4 Data Item 040 Measured Position in Slant Polar Coordinates
        if fspec[3] == True:
            message = remaining_line.pop(0)+" "+remaining_line.pop(0)+" "+remaining_line.pop(0)+" "+remaining_line.pop(0)
            rho, theta = get_measured_position_in_slant_coordinates(message)
            new_csv_line  = new_csv_line +";"+ str(rho)+";"+str(theta)
        elif fspec[3] == False:
            rho = theta = "N/A"
            new_csv_line =  new_csv_line +";"+ str(rho)+";"+str(theta)
    # 5 Data Item 070 Mode 3A Code in Octal Representation
        if fspec[4] == True:
            message = remaining_line.pop(0)+" "+remaining_line.pop(0)
            V, G, L, mode_3a_code = get_mode3a_code(message)
            new_csv_line  = new_csv_line +";"+ str(V)+";"+str(G)+";"+str(mode_3a_code)
        elif fspec[4] == False:
            V = G = L = mode_3a_code = "N/A"
            new_csv_line = new_csv_line +";"+ str(V)+";"+str(G)+";"+str(mode_3a_code)
    # 6 Data Item 090 Flight Level in Binary Representation
        if fspec[5] == True:
            message = remaining_line.pop(0)+" "+remaining_line.pop(0)
            V, G, flight_level = get_flight_level(message)
            new_csv_line = new_csv_line +";"+ str(V)+";"+str(G)+";"+str(flight_level)
        elif fspec[5] == False:
            V = G = flight_level = "N/A"
            new_csv_line = new_csv_line +";"+ str(V)+";"+str(G)+";"+str(flight_level)
    # 7 Data Item 130 Radar Plot Characteristics
        if fspec[6] == True:
            message = remaining_line
            result, remaining_line_130 = get_radar_plot_characteristics(message)
            remaining_line = remaining_line_130
            
            # Iterate over the result dictionary and add each value to the CSV line
            for key, value in result.items():
                new_csv_line = new_csv_line + ";" + str(value)
        elif fspec[6] == False:
            new_csv_line = new_csv_line + ";" + "N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;"
    # 8 Data Item 220 Aircraft Address
        if fspec[7] == True:
            message = remaining_line.pop(0) + " " + remaining_line.pop(0) + " " + remaining_line.pop(0)
            ta = get_aircraft_address(message)
            new_csv_line = new_csv_line +";" + str(ta)
        elif fspec[7] == False:
            ta = "N/A"
            new_csv_line = new_csv_line +";" + str(ta)
    # 9 Data Item 240 Aircraft Identification
        if fspec[8] == True:
            message = remaining_line.pop(0) + " " + remaining_line.pop(0) + " " + remaining_line.pop(0) + " "+remaining_line.pop(0) + " " + remaining_line.pop(0) + " " + remaining_line.pop(0)
            ia = get_aircraft_identification(message)
            new_csv_line = new_csv_line+";" + str(ia)
        elif fspec[8] ==  False:
            ia = "N/A"
            new_csv_line = new_csv_line+";" + str(ia)
    # 10 Data Item 250 Mode S MB Data
        if fspec[9] == True:
            ModesPresent, resultBDS4, resultBDS5, resultBDS6, remaining_line_250 = get_mode_s_mb_data(remaining_line)
            remaining_line = remaining_line_250
                
            for key, value in resultBDS4.items():
                new_csv_line = new_csv_line + ";" + str(value)
            for key, value in resultBDS5.items():
                new_csv_line = new_csv_line + ";" + str(value)
            for key, value in resultBDS6.items():
                new_csv_line = new_csv_line + ";" + str(value)
        elif fspec[9] == False:
            new_csv_line = new_csv_line + ";N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A"
    # 11 Data Item 161 Track Number
        if fspec[10] ==  True:
            message = remaining_line.pop(0) +" "+remaining_line.pop(0)
            track_number = get_track_number(message)
            new_csv_line = new_csv_line + ";" + str(track_number)
        elif fspec[10] == False:
            new_csv_line = new_csv_line + ";N/A"
    # 12 Data Item 042 Calculated Position in Cartesian Coordinates
        if fspec[11] ==  True:
            message = remaining_line.pop(0) +" "+remaining_line.pop(0)+" "+remaining_line.pop(0) +" "+remaining_line.pop(0)
            x, y = get_track_number(message)
            new_csv_line = new_csv_line + ";" + str(x)+ ";" + str(y)
        elif fspec[11] == False:
            new_csv_line = new_csv_line + ";N/A;N/A"



        csv_lines.append(new_csv_line)    
        i = i+1
    # Write the CSV lines to a file if needed
    with open("output.csv", "w") as csv_file:
         csv_file.write("\n".join(csv_lines))
        
# Missing to insert the latitude longitude and height at the position expected in csv, also missing mode c?

convert_to_csv("assets/test.ast")