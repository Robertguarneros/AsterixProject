import math
import re

import numpy as np


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
                new_line = (
                    cat_binary + " " + length_binary_1 + " " + length_binary_2 + " "
                )

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
            unused_octets = separated_line[i + 1 :]  # Store remaining unread octets
            break

    # Remove spaces in FSPEC string
    fspec = fspec.replace(" ", "")

    # Parse the FSPEC bits
    for i, bit in enumerate(fspec):
        if i in {7, 15, 23, 31}:
            # Skip specific positions (as per your current logic)
            pass
        else:
            # Append True for '1' and False for '0'
            if bit == "1":
                DataItems.append(True)
            elif bit == "0":
                DataItems.append(False)

    # Ensure DataItems has exactly 21 elements by appending False as needed
    while len(DataItems) < 21:
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
    total_seconds = round(time_of_day / 128)

    # Calculamos horas, minutos y segundos
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = total_seconds % 60

    time = f"{hours:02}:{minutes:02}:{seconds:06.3f}"

    # Retornamos los valores calculados
    return time, total_seconds


# Decode 020
def get_target_report_descriptor(message):
    # Initialize all values
    TYP = SIM = RDP = SPI = RAB = TST = ERR = XPP = ME = MI = FOE_FRI = ADSB_EP = (
        ADSB_VAL
    ) = SCN_EP = SCN_VAL = PAI_EP = PAI_VAL = None

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
    sim = first_octet[3]  # Bit 5 (SIM)
    rdp = first_octet[4]  # Bit 4 (RDP)
    spi = first_octet[5]  # Bit 3 (SPI)
    rab = first_octet[6]  # Bit 2 (RAB)
    FX1 = first_octet[7]  # Bit 1 (FX of first octet)

    # Interpret the values of TYP
    typ_meaning = {
        "000": "No detection",
        "001": "Single PSR detection",
        "010": "Single SSR detection",
        "011": "SSR + PSR detection",
        "100": "Single ModeS All-Call",
        "101": "Single ModeS Roll-Call",
        "110": "ModeS All-Call + PSR",
        "111": "ModeS Roll-Call + PSR",
    }

    # Save results of the first octet
    TYP = typ_meaning.get(typ, "Unknown Detection Type")  # Detection type
    SIM = (
        "Simulated target report" if sim == "1" else "Actual target report"
    )  # Target report
    RDP = "RDP Chain 2" if rdp == "1" else "RDP Chain 1"  # Report from RDP
    SPI = (
        "Presence of SPI" if spi == "1" else "Absence of SPI"
    )  # Special Position Identification
    RAB = (
        "Report from field monitor (fixed transponder)"
        if rab == "1"
        else "Report from aircraft transponder"
    )

    # If FX1 is 1, we need to decode the second octet
    if FX1 == "1" and len(unused_octets) > 0:
        second_octet = octets[1]
        unused_octets.pop(0)  # Remove the second octet from unused_octets

        # Decode the second octet
        tst = second_octet[0]  # Bit 8 (TST)
        err = second_octet[1]  # Bit 7 (ERR)
        xpp = second_octet[2]  # Bit 6 (XPP)
        me = second_octet[3]  # Bit 5 (ME)
        mi = second_octet[4]  # Bit 4 (MI)
        foe_fri = second_octet[5:7]  # Bits 3/2 (FOE/FRI)
        FX2 = second_octet[7]  # Bit 1 (FX of second octet)

        # Interpret FOE/FRI
        foe_fri_meaning = {
            "00": "No Mode 4 interrogation",
            "01": "Friendly target",
            "10": "Unknown target",
            "11": "No reply",
        }

        # Save results of the second octet
        TST = "Test target report" if tst == "1" else "Real target report"
        ERR = "Extended Range present" if err == "1" else "No Extended Range"
        XPP = "X-Pulse present" if xpp == "1" else "No X-Pulse present"
        ME = "Military emergency" if me == "1" else "No military emergency"
        MI = "Military identification" if mi == "1" else "No military identification"
        FOE_FRI = foe_fri_meaning.get(foe_fri, "Error decoding FOE/FRI")

        # If FX2 is 1, we need to decode the third octet
        if FX2 == "1" and len(unused_octets) > 0:
            third_octet = octets[2]
            unused_octets.pop(0)  # Remove the third octet from unused_octets

            # Decode the third octet
            adsb_ep = third_octet[0]  # Bit 8 (ADSB#EP)
            adsb_val = third_octet[1]  # Bit 7 (ADSB#VAL)
            scn_ep = third_octet[2]  # Bit 6 (SCN#EP)
            scn_val = third_octet[3]  # Bit 5 (SCN#VAL)
            pai_ep = third_octet[4]  # Bit 4 (PAI#EP)
            pai_val = third_octet[5]  # Bit 3 (PAI#VAL)
            FX3 = third_octet[7]  # Bit 2 (FX of third octet)
            _ = FX3
            # Save results of the third octet
            ADSB_EP = "ADSB populated" if adsb_ep == "1" else "ADSB not populated"
            ADSB_VAL = "Available" if adsb_val == "1" else "Not Available"
            SCN_EP = "SCN populated" if scn_ep == "1" else "SCN not populated"
            SCN_VAL = "Available" if scn_val == "1" else "Not Available"
            PAI_EP = "PAI populated" if pai_ep == "1" else "PAI not populated"
            PAI_VAL = "Available" if pai_val == "1" else "Not Available"

    # Return all decoded fields and the remaining unused octets
    return (
        TYP,
        SIM,
        RDP,
        SPI,
        RAB,
        TST,
        ERR,
        XPP,
        ME,
        MI,
        FOE_FRI,
        ADSB_EP,
        ADSB_VAL,
        SCN_EP,
        SCN_VAL,
        PAI_EP,
        PAI_VAL,
        unused_octets,
    )


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
    V = (
        "Code not validated" if first_octet_bin[0] == "1" else "Code Validated"
    )  # Bit 16: Validación (V)
    G = (
        "Garbled code" if first_octet_bin[1] == "1" else "Default"
    )  # Bit 15: Código Garbled (G)
    L = (
        "Mode-3/A code not extracted during the last scan"
        if first_octet_bin[2] == "1"
        else "Mode-3/A code derived from the reply of the transponder"
    )  # Bit 14: Código derivado en la última exploración (L)

    # Extraemos el código Mode-3/A en formato octal de bits 12 a 1 (de A4 a D1)
    A = (
        (int(first_octet_bin[4]) * 4)
        + (int(first_octet_bin[5]) * 2)
        + int(first_octet_bin[6])
    )
    B = (
        (int(first_octet_bin[7]) * 4)
        + (int(second_octet_bin[0]) * 2)
        + int(second_octet_bin[1])
    )
    C = (
        (int(second_octet_bin[2]) * 4)
        + (int(second_octet_bin[3]) * 2)
        + int(second_octet_bin[4])
    )
    D = (
        (int(second_octet_bin[5]) * 4)
        + (int(second_octet_bin[6]) * 2)
        + int(second_octet_bin[7])
    )

    # Convertimos el código Mode-3/A en una representación octal
    mode_3a_code = f"{A}{B}{C}{D}"

    # Retornamos los valores de los bits de control y el código octal
    return V, G, L, mode_3a_code


# Decode 090
def get_flight_level(message):
    # Split the message into two octets
    first_octet_bin = message.split()[0]  # First octet in binary
    second_octet_bin = message.split()[1]  # Second octet in binary

    # Extract control bits
    V = (
        "Code not validated" if first_octet_bin[0] == "1" else "Code Validated"
    )  # Bit 16: Validation (V)
    G = (
        "Garbled code" if first_octet_bin[1] == "1" else "Default"
    )  # Bit 15: Garbled code (G)

    # Extract the flight level (bits 14 to 1) as a single block
    flight_level_bin = first_octet_bin[2:] + second_octet_bin  # From bits 14 to 1

    # Interpret the flight level binary as a signed 14-bit integer (two's complement)
    if flight_level_bin[0] == "1":  # Negative value
        flight_level = -((1 << 14) - int(flight_level_bin, 2))
    else:  # Positive value
        flight_level = int(flight_level_bin, 2)

    # Convert to the actual flight level using LSB = 1/4 FL
    flight_level *= 0.25

    # Return control bits and the flight level
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
        "SRL": primary_subfield[0] == "1",  # Subfield #1 SSR Plot Runlength
        "SRR": primary_subfield[1]
        == "1",  # Subfield #2 Number of received replies for MSSR
        "SAM": primary_subfield[2] == "1",  # Subfield #3 Amplitude of MSSR reply
        "PRL": primary_subfield[3] == "1",  # Subfield #4 PSR Plot Runlength
        "PAM": primary_subfield[4] == "1",  # Subfield #5 Amplitude of PSR Plot
        "RPD": primary_subfield[5] == "1",  # Subfield #6 Difference in range (PSR-SSR)
        "APD": primary_subfield[6]
        == "1",  # Subfield #7 Difference in azimuth (PSR-SSR)
        "FX": primary_subfield[7] == "1",  # Extension into next octet
    }

    # Initialize results dictionary
    result = {}

    # Start processing octets after the primary subfield
    octet_index = 1

    # Subfield #1 (SSR Plot Runlength)
    if subfields["SRL"] and octet_index < len(octet_list):
        srl_bits = octet_list[octet_index]
        srl_value = int(srl_bits, 2) * (360 / 2**13)
        result["SSR Plot Runlength (degrees)"] = str(srl_value) + " dg"
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
        sam_value = (
            int(sam_bits, 2) if sam_bits[0] == "0" else int(sam_bits, 2) - (1 << 8)
        )
        result["Amplitude of MSSR Reply (dBm)"] = str(sam_value) + " dBm"
        octet_index += 1
    else:
        result["Amplitude of MSSR Reply (dBm)"] = "N/A"

    # Subfield #4 (Primary Plot Runlength)
    if subfields["PRL"] and octet_index < len(octet_list):
        prl_bits = octet_list[octet_index]
        prl_value = int(prl_bits, 2) * (360 / 2**13)
        result["Primary Plot Runlength (degrees)"] = str(prl_value) + " dg"
        octet_index += 1
    else:
        result["Primary Plot Runlength (degrees)"] = "N/A"

    # Subfield #5 (Amplitude of Primary Plot)
    if subfields["PAM"] and octet_index < len(octet_list):
        pam_bits = octet_list[octet_index]
        pam_value = (
            int(pam_bits, 2) if pam_bits[0] == "0" else int(pam_bits, 2) - (1 << 8)
        )
        result["Amplitude of Primary Plot (dBm)"] = str(pam_value) + " dBm"
        octet_index += 1
    else:
        result["Amplitude of Primary Plot (dBm)"] = "N/A"

    # Subfield #6 (Difference in Range between PSR and SSR plot)
    if subfields["RPD"] and octet_index < len(octet_list):
        rpd_bits = octet_list[octet_index]
        rpd_value = (
            int(rpd_bits, 2) if rpd_bits[0] == "0" else int(rpd_bits, 2) - (1 << 8)
        )
        result["Difference in Range (PSR-SSR) (NM)"] = str(rpd_value / 256) + " NM"
        octet_index += 1
    else:
        result["Difference in Range (PSR-SSR) (NM)"] = "N/A"

    # Subfield #7 (Difference in Azimuth between PSR and SSR plot)
    if subfields["APD"] and octet_index < len(octet_list):
        apd_bits = octet_list[octet_index]
        apd_value = (
            int(apd_bits, 2) if apd_bits[0] == "0" else int(apd_bits, 2) - (1 << 8)
        )
        result["Difference in Azimuth (PSR-SSR) (degrees)"] = (
            str(apd_value * (360 / 2**14)) + " dg"
        )
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
    "000001": "A",
    "000010": "B",
    "000011": "C",
    "000100": "D",
    "000101": "E",
    "000110": "F",
    "000111": "G",
    "001000": "H",
    "001001": "I",
    "001010": "J",
    "001011": "K",
    "001100": "L",
    "001101": "M",
    "001110": "N",
    "001111": "O",
    "010000": "P",
    "010001": "Q",
    "010010": "R",
    "010011": "S",
    "010100": "T",
    "010101": "U",
    "010110": "V",
    "010111": "W",
    "011000": "X",
    "011001": "Y",
    "011010": "Z",
    "110000": "0",
    "110001": "1",
    "110002": "2",
    "110011": "3",
    "110100": "4",
    "110101": "5",
    "110110": "6",
    "110111": "7",
    "111000": "8",
    "111001": "9",
    "100000": " ",  # Space
}


# Decode 240
def get_aircraft_identification(bytes_str):
    # Remove spaces from the input string
    bytes_str = bytes_str.replace(" ", "")

    # Iterate over the binary string in 6-bit chunks
    ascii_result = ""
    for i in range(0, len(bytes_str), 6):
        byte = bytes_str[i : i + 6]

        # Convert the 6-bit binary to a character using the dictionary
        if byte in six_bit_to_char:
            ascii_result += six_bit_to_char[byte]
        else:
            ascii_result += "?"  # Handle any invalid 6-bit chunks
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
        "TARGET ALT SOURCE": "N/A",
    }

    resultBDS5 = {
        "Roll Angle": "N/A",
        "True Track Angle": "N/A",
        "Ground Speed": "N/A",
        "Track Angle Rate": "N/A",
        "True Airspeed": "N/A",
    }

    resultBDS6 = {
        "MAGNETIC HEADING": "N/A",
        "Indicated Airspeed": "N/A",
        "Mach Number": "N/A",
        "Barometric Altitude Rate": "N/A",
        "Inertial Vertical Speed": "N/A",
    }

    # Process each BDS item
    for item in BDSItems:
        # Combine 8 octets into one bit string for easier bit manipulation
        item_bits = "".join(item)

        BDS1 = int(item_bits[56:60], 2)
        BDS2 = int(item_bits[60:64], 2)
        BDSTotal = f"{BDS1},{BDS2}"
        ModesPresent.append("BDS:" + BDSTotal)

        if BDSTotal == "4,0":
            # Populate only the required values from BDS 4.0
            resultBDS4["MCP/FCU SELECTED ALTITUDE"] = int(item_bits[1:13], 2) * 16
            resultBDS4["FMS SELECTED ALTITUDE"] = int(item_bits[14:26], 2) * 16
            resultBDS4["BAROMETRIC PRESSURE SETTING"] = (
                int(item_bits[27:39], 2) * 0.1 + 800
            )
            resultBDS4["VNAV MODE"] = (
                "Active" if item_bits[49:50] == "1" else "Not Active"
            )
            resultBDS4["ALT HOLD MODE"] = (
                "Active" if item_bits[50:51] == "1" else "Not Active"
            )
            resultBDS4["APPROACH MODE"] = (
                "Active" if item_bits[51:52] == "1" else "Not Active"
            )
            target_alt_source_mapping = {
                "00": "Unknown",
                "01": "Aircraft Altitude",
                "10": "FCU/MCP Selected Altitude",
                "11": "FMS Selected Altitude",
            }
            resultBDS4["TARGET ALT SOURCE"] = target_alt_source_mapping.get(
                item_bits[54:56], "Unknown"
            )

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
            resultBDS6["Barometric Altitude Rate"] = barometric_altitude_rate * (
                8192 / 256
            )

            inertial_vertical_speed = int(item_bits[46:56], 2)
            if inertial_vertical_speed >= 2**9:
                inertial_vertical_speed -= 2**10
            resultBDS6["Inertial Vertical Speed"] = inertial_vertical_speed * (
                8192 / 256
            )

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
    x_int = int(x_bin, 2) if x_bin[0] == "0" else int(x_bin, 2) - (1 << 16)
    y_int = int(y_bin, 2) if y_bin[0] == "0" else int(y_bin, 2) - (1 << 16)

    # The LSB is 1/128 NM, so divide by 128 to get the final value in NM
    x_nm = x_int / 128.0
    y_nm = y_int / 128.0

    return x_nm, y_nm


# Decode 200
def get_calculated_track_velocity(bytes):

    binary_octets = bytes.split()

    data = [int(octet, 2) for octet in binary_octets]

    groundspeed_raw = (data[0] << 8) + data[1]  # Combina octeto 1 y octeto 2

    heading_raw = (data[2] << 8) + data[3]  # Combina octeto 3 y octeto 4

    # El LSB es 2^-14 NM/s, 0.22 nudos por bit
    groundspeed = (
        groundspeed_raw * (2**-14) * 3600
    )  # Convertir de NM/s a nudos (1 NM/s = 3600 NM/h = 3600 knots)

    # El LSB es 360° / 2^16, 0.0055 grados por bit
    heading = heading_raw * (360 / 65536)  # 2^16 = 65536

    return groundspeed, heading


# Decode 170
def get_track_status(octet_list):

    result = {}

    # First octet processing
    first_octet = octet_list[0]

    CNF = int(first_octet[0])
    RAD = int(first_octet[1:3], 2)  # Bits 7/6
    DOU = int(first_octet[3])  # Bit 5
    MAH = int(first_octet[4])  # Bit 4
    CDM = int(first_octet[5:7], 2)  # Bits 3/2
    FX = int(first_octet[7])  # Bit 1 (LSB)

    # Set results with default N/A if unknown
    result["CNF"] = "Tentative Track" if CNF == 1 else "Confirmed Track"

    if RAD == 0:
        result["RAD"] = "Combined Track"
    elif RAD == 1:
        result["RAD"] = "PSR Track"
    elif RAD == 2:
        result["RAD"] = "SSR/Mode S Track"
    else:
        result["RAD"] = "N/A"

    result["DOU"] = "Low confidence" if DOU == 1 else "Normal confidence"
    result["MAH"] = (
        "Horizontal maneuver sensed" if MAH == 1 else "No horizontal maneuver sensed"
    )

    if CDM == 0:
        result["CDM"] = "Maintaining"
    elif CDM == 1:
        result["CDM"] = "Climbing"
    elif CDM == 2:
        result["CDM"] = "Descending"
    else:
        result["CDM"] = "N/A"

    # Track how many octets were used
    used_octets = 1

    # Initialize extended fields as "N/A" in case they are not provided
    result["TRE"] = "N/A"
    result["GHO"] = "N/A"
    result["SUP"] = "N/A"
    result["TCC"] = "N/A"

    # Check if FX (extension bit) is set
    if FX == 1:
        # Extended information available, reset to empty list
        result["TRE"] = []
        result["GHO"] = []
        result["SUP"] = []
        result["TCC"] = []

        # Loop through additional octets as long as FX is set
        for i in range(1, len(octet_list)):
            current_octet = octet_list[i]

            # Decode additional octet bits
            TRE = int(current_octet[0])
            GHO = int(current_octet[1])
            SUP = int(current_octet[2])
            TCC = int(current_octet[3])
            FX = int(
                current_octet[7]
            )  # Check the FX bit again to see if more octets follow

            # Append decoded values to results
            result["TRE"].append("End of track" if TRE == 1 else "Track still alive")
            result["GHO"].append("Ghost target" if GHO == 1 else "True target")
            result["SUP"].append(
                "Track maintained by neighboring node"
                if SUP == 1
                else "No neighboring node"
            )
            result["TCC"].append(
                "Slant range correction" if TCC == 1 else "Radar plane tracking"
            )

            used_octets += 1

            # Break the loop if FX is not set (no more octets)
            if FX == 0:
                break

    # Return remaining octets that were not used
    remaining_octets = octet_list[used_octets:]

    # If the extended fields are empty (no additional info), set them to "N/A"
    if not result["TRE"]:
        result["TRE"] = "N/A"
    if not result["GHO"]:
        result["GHO"] = "N/A"
    if not result["SUP"]:
        result["SUP"] = "N/A"
    if not result["TCC"]:
        result["TCC"] = "N/A"

    return result, remaining_octets


# Decode 110
def get_height_measured(bytes):

    binary_octets = bytes.split()

    octet1 = binary_octets[0]
    octet2 = int(binary_octets[1], 2)  # Segundo octeto a entero

    # Ignorar los dos primeros bits del primer octeto y obtener los 14 bits restantes
    height_raw = ((int(octet1, 2) & 0x3FFF) << 8) | octet2

    if (
        int(octet1, 2) & 0x20
    ) != 0:  # Si el bit 14 (tercer bit) está activado, es negativo
        height_raw -= 1 << 14  # Complemento a dos (valor negativo)

    # Convertir la altura a pies (cada unidad = 25 ft)
    height_feet = height_raw * 25

    return height_feet


# Decode 230
def get_comms(bytes):

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
    B1A = second_octet[3]  # Bit 5
    B1B = second_octet[4:8]  # Bits 4-1

    if COM == 0:
        result["COM"] = "No communications capability (surveillance only)"
    elif COM == 1:
        result["COM"] = "Comm. A and Comm. B capability"
    elif COM == 2:
        result["COM"] = "Comm. A, Comm. B and Uplink ELM"
    elif COM == 3:
        result["COM"] = "Comm. A, Comm. B, Uplink ELM and Downlink ELM"
    elif COM == 4:
        result["COM"] = "Level 5 Transponder capability"
    else:
        result["COM"] = "Not assigned"

    if STAT == 0:
        result["STAT"] = "No alert, no SPI, aircraft airborne"
    elif STAT == 1:
        result["STAT"] = "No alert, no SPI, aircraft on ground"
    elif STAT == 2:
        result["STAT"] = "Alert, no SPI, aircraft airborne"
    elif STAT == 3:
        result["STAT"] = "Alert, no SPI, aircraft on ground"
    elif STAT == 4:
        result["STAT"] = "Alert, SPI, aircraft airborne or on ground"
    elif STAT == 5:
        result["STAT"] = "No alert, SPI, aircraft airborne or on ground"
    elif STAT == 7:
        result["STAT"] = "Unknown"
    else:
        result["STAT"] = "Not assigned"

    result["SI"] = "II-Code Capable" if SI == 1 else "SI-Code Capable"

    result["MSSC"] = "Yes" if MSSC == 1 else "No"

    result["ARC"] = "25 ft resolution" if ARC == 1 else "100 ft resolution"

    result["AIC"] = "Yes" if AIC == 1 else "No"

    result["B1A"] = "BDS 1,0 bit 16 = " + B1A

    result["B1B"] = "BDS 1,0 bits 37/40 = " + B1B

    return result


# Constants
A = 6378137.0  # Semi-major axis in meters
E2 = 0.00669437999014  # Eccentricity squared for WGS84
B = 6356752.3142  # Semi-minor axis in meters


def calculate_rotation_matrix(lat, lon):
    """
    Calculates the rotation matrix for given latitude and longitude (in radians).
    """
    r11 = -np.sin(lon)
    r12 = np.cos(lon)
    r13 = 0
    r21 = -np.sin(lat) * np.cos(lon)
    r22 = -np.sin(lat) * np.sin(lon)
    r23 = np.cos(lat)
    r31 = np.cos(lat) * np.cos(lon)
    r32 = np.cos(lat) * np.sin(lon)
    r33 = np.sin(lat)
    return np.array([[r11, r12, r13], [r21, r22, r23], [r31, r32, r33]])


def calculate_translation_matrix(lat, lon, alt):
    """
    Calculates the translation matrix for a given latitude, longitude (in radians), and altitude (in meters).
    """
    nu = A / np.sqrt(1 - E2 * np.sin(lat) ** 2)
    tx = (nu + alt) * np.cos(lat) * np.cos(lon)
    ty = (nu + alt) * np.cos(lat) * np.sin(lon)
    tz = (nu * (1 - E2) + alt) * np.sin(lat)
    return np.array([tx, ty, tz])


def polar_to_cartesian(rho, theta, elevation):
    """
    Converts polar coordinates (ρ, θ, elevation) to Cartesian (x, y, z).
    ρ is in meters, θ and elevation are in radians.
    """
    x = rho * np.cos(elevation) * np.sin(theta)
    y = rho * np.cos(elevation) * np.cos(theta)
    z = rho * np.sin(elevation)
    return np.array([x, y, z])


def cartesian_to_geocentric(cartesian_coords, radar_coords):
    """
    Converts local Cartesian coordinates to geocentric coordinates using radar's position.
    """
    lat, lon, alt = radar_coords
    translation_matrix = calculate_translation_matrix(lat, lon, alt)
    rotation_matrix = calculate_rotation_matrix(lat, lon)
    rotated_vector = np.matmul(rotation_matrix.T, cartesian_coords)
    geocentric_coords = rotated_vector + translation_matrix
    return geocentric_coords


def geocentric_to_geodesic(c):
    """
    Converts geocentric (x, y, z) to geodetic coordinates (latitude, longitude, height).
    """
    x, y, z = c
    d_xy = np.sqrt(x**2 + y**2)

    if abs(x) < 1e-10 and abs(y) < 1e-10:
        lat = np.pi / 2.0 if z >= 0 else -np.pi / 2.0
        lon = 0
        alt = abs(z) - B
    else:
        lat = np.arctan((z / d_xy) / (1 - (A * E2) / np.sqrt(d_xy**2 + z**2)))
        nu = A / np.sqrt(1 - E2 * np.sin(lat) ** 2)
        alt = (d_xy / np.cos(lat)) - nu
        Lat_over = -0.1 if lat >= 0 else 0.1

        # Iterative refinement
        loop_count = 0
        while abs(lat - Lat_over) > 1e-12 and loop_count < 50:
            Lat_over = lat
            lat = np.arctan((z * (1 + alt / nu)) / (d_xy * ((1 - E2) + (alt / nu))))
            nu = A / np.sqrt(1 - E2 * np.sin(lat) ** 2)
            alt = d_xy / np.cos(lat) - nu
            loop_count += 1

        lon = np.arctan2(y, x)

    return np.degrees(lat), np.degrees(lon), alt


# Function that processes all the data items in a single line
def convert_to_csv(input_file, output_file):
    lines = read_and_split_binary(input_file)
    csv_lines = []
    new_csv_line = "NUM;SAC;SIC;TIME;TIME(s);LAT;LON;H;TYP_020;SIM_020;RDP_020;SPI_020;RAB_020;TST_020;ERR_020;XPP_020;ME_020;MI_020;FOE_FRI_020;RHO;THETA;V_070;G_070;MODE 3/A;V_090;G_090;FL;MODE C Corrected Altitude;SRL_130;SSR_130;SAM_130;PRL_130;PAM_130;RPD_130;APD_130;TA;TI;MCP_ALT;FMS_ALT;BP;VNAV;ALT_HOLD;APP;TARGET_ALT_SOURCE;RA;TTA;GS;TAR;TAS;HDG;IAS;MACH;BAR;IVV;TN;X;Y;GS_KT;HEADING;CNF_170;RAD_170;DOU_170;MAH_170;CDM_170;TRE_170;GHO_170;SUP_170;TCC_170;HEIGHT;COM_230;STAT_230;SI_230;MSCC_230;ARC_230;AIC_230;B1A_230;B1B_230"
    csv_lines.append(new_csv_line)
    i = 1
    for line in lines:
        new_csv_line = str(i) + ";"
        fspec, remaining_line = get_fspec(line)
        try:
            # 1 Data Item 010 SAC, SIC
            if fspec[0]:
                try:
                    message = remaining_line.pop(0) + " " + remaining_line.pop(0)
                    sac, sic = get_sac_sic(message)
                    new_csv_line = new_csv_line + str(sac) + ";" + str(sic) + ";"
                except IndexError:
                    new_csv_line += "N/A;N/A;"
            elif not fspec[0]:
                sac = sic = "N/A"
                new_csv_line = new_csv_line + str(sac) + ";" + str(sic) + ";"
            # 2 Data Item 140 Time of Day
            if fspec[1]:
                try:
                    message = (
                        remaining_line.pop(0)
                        + " "
                        + remaining_line.pop(0)
                        + " "
                        + remaining_line.pop(0)
                    )
                    time, total_seconds = get_time_of_day(message)
                    new_csv_line = new_csv_line + str(time) + ";" + str(total_seconds)
                except IndexError:
                    new_csv_line += "N/A;N/A"
            elif not fspec[1]:
                time = total_seconds = "N/A"
                new_csv_line = new_csv_line + str(time) + ";" + str(total_seconds)

            # Temporary placeholder for lat, lon and height
            new_csv_line += ";LAT;LON;H"
            # 3 Data Item 020 Target Report Descriptor
            if fspec[2]:
                try:
                    message = remaining_line
                    (
                        TYP,
                        SIM,
                        RDP,
                        SPI,
                        RAB,
                        TST,
                        ERR,
                        XPP,
                        ME,
                        MI,
                        FOE_FRI,
                        ADSB_EP,
                        ADSB_VAL,
                        SCN_EP,
                        SCN_VAL,
                        PAI_EP,
                        PAI_VAL,
                        remaining_line_040,
                    ) = get_target_report_descriptor(message)
                    new_csv_line = (
                        new_csv_line
                        + ";"
                        + str(TYP)
                        + ";"
                        + str(SIM)
                        + ";"
                        + str(RDP)
                        + ";"
                        + str(SPI)
                        + ";"
                        + str(RAB)
                        + ";"
                        + str(TST)
                        + ";"
                        + str(ERR)
                        + ";"
                        + str(XPP)
                        + ";"
                        + str(ME)
                        + ";"
                        + str(MI)
                        + ";"
                        + str(FOE_FRI)
                    )
                    remaining_line = remaining_line_040
                except IndexError:
                    new_csv_line += ";N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A"
            elif not fspec[2]:
                TYP = SIM = RDP = SPI = RAB = TST = ERR = XPP = ME = MI = FOE_FRI = (
                    "N/A"
                )
                new_csv_line = (
                    new_csv_line
                    + ";"
                    + str(TYP)
                    + ";"
                    + str(SIM)
                    + ";"
                    + str(RDP)
                    + ";"
                    + str(SPI)
                    + ";"
                    + str(RAB)
                    + ";"
                    + str(TST)
                    + ";"
                    + str(ERR)
                    + ";"
                    + str(XPP)
                    + ";"
                    + str(ME)
                    + ";"
                    + str(MI)
                    + ";"
                    + str(FOE_FRI)
                )
            # 4 Data Item 040 Measured Position in Slant Polar Coordinates
            if fspec[3]:
                try:
                    message = (
                        remaining_line.pop(0)
                        + " "
                        + remaining_line.pop(0)
                        + " "
                        + remaining_line.pop(0)
                        + " "
                        + remaining_line.pop(0)
                    )
                    rho, theta = get_measured_position_in_slant_coordinates(message)
                    rho_measurement = rho
                    new_csv_line = new_csv_line + ";" + str(rho) + ";" + str(theta)
                except IndexError:
                    new_csv_line += ";N/A;N/A"
            elif not fspec[3]:
                rho = theta = "N/A"
                new_csv_line = new_csv_line + ";" + str(rho) + ";" + str(theta)
            # 5 Data Item 070 Mode 3A Code in Octal Representation
            if fspec[4]:
                try:
                    message = remaining_line.pop(0) + " " + remaining_line.pop(0)
                    V, G, L, mode_3a_code = get_mode3a_code(message)
                    new_csv_line = (
                        new_csv_line
                        + ";"
                        + str(V)
                        + ";"
                        + str(G)
                        + ";"
                        + str(mode_3a_code)
                    )
                except IndexError:
                    new_csv_line += ";N/A;N/A;N/A"
            elif not fspec[4]:
                V = G = L = mode_3a_code = "N/A"
                _ = L
                new_csv_line = (
                    new_csv_line + ";" + str(V) + ";" + str(G) + ";" + str(mode_3a_code)
                )
            # 6 Data Item 090 Flight Level in Binary Representation
            if fspec[5]:
                try:
                    message = remaining_line.pop(0) + " " + remaining_line.pop(0)
                    V, G, flight_level = get_flight_level(message)
                    new_csv_line = (
                        new_csv_line
                        + ";"
                        + str(V)
                        + ";"
                        + str(G)
                        + ";"
                        + str(flight_level)
                    )
                except IndexError:
                    new_csv_line += ";N/A;N/A;N/A"
            elif not fspec[5]:
                V = G = flight_level = "N/A"
                new_csv_line = (
                    new_csv_line + ";" + str(V) + ";" + str(G) + ";" + str(flight_level)
                )
            # Temporary placeholder for mode c corrected
            new_csv_line += ";MODE C corrected"
            # 7 Data Item 130 Radar Plot Characteristics
            if fspec[6]:
                try:
                    message = remaining_line
                    result, remaining_line_130 = get_radar_plot_characteristics(message)
                    remaining_line = remaining_line_130
                    # Iterate over the result dictionary and add each value to the CSV line
                    for key, value in result.items():
                        new_csv_line = new_csv_line + ";" + str(value)
                except IndexError:
                    new_csv_line += ";N/A;N/A;N/A;N/A;N/A;N/A;N/A"
            elif not fspec[6]:
                new_csv_line = new_csv_line + ";" + "N/A;N/A;N/A;N/A;N/A;N/A;N/A"
            # 8 Data Item 220 Aircraft Address
            if fspec[7]:
                try:
                    message = (
                        remaining_line.pop(0)
                        + " "
                        + remaining_line.pop(0)
                        + " "
                        + remaining_line.pop(0)
                    )
                    ta = get_aircraft_address(message)
                    new_csv_line = new_csv_line + ";" + str(ta)
                except IndexError:
                    new_csv_line += ";N/A"
            elif not fspec[7]:
                new_csv_line += ";N/A"
            # 9 Data Item 240 Aircraft Identification
            if fspec[8]:
                try:
                    message = (
                        remaining_line.pop(0)
                        + " "
                        + remaining_line.pop(0)
                        + " "
                        + remaining_line.pop(0)
                        + " "
                        + remaining_line.pop(0)
                        + " "
                        + remaining_line.pop(0)
                        + " "
                        + remaining_line.pop(0)
                    )
                    ia = get_aircraft_identification(message)
                    new_csv_line = new_csv_line + ";" + str(ia)
                except IndexError:
                    new_csv_line += ";N/A"
            elif not fspec[8]:
                new_csv_line += ";N/A"
            # 10 Data Item 250 Mode S MB Data
            if fspec[9]:
                try:
                    (
                        ModesPresent,
                        resultBDS4,
                        resultBDS5,
                        resultBDS6,
                        remaining_line_250,
                    ) = get_mode_s_mb_data(remaining_line)
                    remaining_line = remaining_line_250

                    for key, value in resultBDS4.items():
                        new_csv_line = new_csv_line + ";" + str(value)
                    for key, value in resultBDS5.items():
                        new_csv_line = new_csv_line + ";" + str(value)
                    for key, value in resultBDS6.items():
                        new_csv_line = new_csv_line + ";" + str(value)
                except IndexError:
                    new_csv_line += ";N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A"
            elif not fspec[9]:
                new_csv_line = (
                    new_csv_line
                    + ";N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A"
                )
            # Mode C corrected Altitude
            try:
                altitude_in_feet_corrected = (
                    0  # Default value in case conditions are not met
                )
                if resultBDS4.get("BAROMETRIC PRESSURE SETTING") != "N/A":
                    QNH_actual = float(resultBDS4.get("BAROMETRIC PRESSURE SETTING"))
                    QNH_standard = 1013.2
                    if float(flight_level) < 60:
                        if 1013 <= QNH_actual <= 1013.3:
                            new_csv_line = new_csv_line.replace("MODE C corrected", "")
                        else:
                            altitude_in_feet_corrected = (
                                float((flight_level) * 100)
                                + (QNH_actual - QNH_standard) * 30
                            )
                            altitude_in_feet_corrected = round(
                                altitude_in_feet_corrected, 2
                            )
                            new_csv_line = new_csv_line.replace(
                                "MODE C corrected", str(altitude_in_feet_corrected)
                            )
                    else:
                        new_csv_line = new_csv_line.replace("MODE C corrected", "")

                else:
                    new_csv_line = new_csv_line.replace("MODE C corrected", "")
            except ValueError:
                new_csv_line = new_csv_line.replace("MODE C corrected", "")
            # Calculate height / elevation
            try:
                H = 0.0  # Altitude of the Aircraft
                El = 0  # Elevation
                Rti = 6371000.0  # Earth Radius at the Radar Position
                Hri = 2.007 + 25.25  # Altitude of ith Radar
                rho = float(rho) * 1852  # Convert from NM to meters
                if flight_level == "N/A":
                    H = 0
                elif float(flight_level) < 60:
                    if 1013 <= QNH_actual <= 1013.3:
                        H = float((flight_level) * 100 * 0.3048)
                    else:
                        H = float(altitude_in_feet_corrected) * 0.3048
                else:
                    H = float((flight_level) * 100 * 0.3048)
                num = 2 * Rti * (H - Hri) + H**2 - Hri**2 - rho**2
                den = 2 * rho * (Rti + Hri)
                El = math.asin(num / den)
            except ValueError:
                print("Error calculating height in line " + str(i))
            # Calculate Latitude and Longitude and Height
            try:
                if El != 0:
                    radar_coords = (
                        np.radians(41.3007023),
                        np.radians(2.1020588),
                        2.007 + 25.25,
                    )  # Latitude, Longitude in radians, height in meters
                    polar_coords = (
                        float(rho_measurement) * 1852,
                        np.radians(float(theta)),
                        El,
                    )  # Rho in meters, theta in radians, elevation in radians

                    cartesian_coords = polar_to_cartesian(*polar_coords)
                    geocentric_coords = cartesian_to_geocentric(
                        cartesian_coords, radar_coords
                    )
                    lat, lon, alt = geocentric_to_geodesic(geocentric_coords)

                    new_csv_line = new_csv_line.replace(
                        "LAT;LON;H", str(lat) + ";" + str(lon) + ";" + str(alt)
                    )
                else:
                    new_csv_line = new_csv_line.replace("LAT;LON;H", "N/A;N/A;N/A")
            except ValueError:
                new_csv_line = new_csv_line.replace("LAT;LON;H", "N/A;N/A;N/A")
            # 11 Data Item 161 Track Number
            if fspec[10]:
                try:
                    message = remaining_line.pop(0) + " " + remaining_line.pop(0)
                    track_number = get_track_number(message)
                    new_csv_line = new_csv_line + ";" + str(track_number)
                except IndexError:
                    new_csv_line += ";N/A"
            elif not fspec[10]:
                new_csv_line = new_csv_line + ";N/A"
            # 12 Data Item 042 Calculated Position in Cartesian Coordinates
            if fspec[11]:
                try:
                    message = (
                        remaining_line.pop(0)
                        + " "
                        + remaining_line.pop(0)
                        + " "
                        + remaining_line.pop(0)
                        + " "
                        + remaining_line.pop(0)
                    )
                    x, y = get_track_number(message)
                    new_csv_line = new_csv_line + ";" + str(x) + ";" + str(y)
                except IndexError:
                    new_csv_line += ";N/A;N/A"
            elif not fspec[11]:
                new_csv_line = new_csv_line + ";N/A;N/A"
            # 13 Data Item 200 Calculated Track Velocity in Polar Representation
            if fspec[12]:
                try:
                    message = (
                        remaining_line.pop(0)
                        + " "
                        + remaining_line.pop(0)
                        + " "
                        + remaining_line.pop(0)
                        + " "
                        + remaining_line.pop(0)
                    )
                    groundspeed, heading = get_calculated_track_velocity(message)
                    new_csv_line = (
                        new_csv_line + ";" + str(groundspeed) + ";" + str(heading)
                    )
                except IndexError:
                    new_csv_line += ";N/A;N/A"
            elif not fspec[12]:
                new_csv_line = new_csv_line + ";N/A;N/A"
            # 14 Data Item 170 Track Status
            if fspec[13]:
                try:
                    result, remaining_line_170 = get_track_status(remaining_line)
                    remaining_line = remaining_line_170
                    for key, value in result.items():
                        new_csv_line = new_csv_line + ";" + str(value)
                except IndexError:
                    new_csv_line += ";N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A"
            elif not fspec[13]:
                new_csv_line += ";N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A"
            # 15 Data Item 210 Track Quality Not needed
            if fspec[14]:
                removed_octets = (
                    remaining_line.pop(0)
                    + " "
                    + remaining_line.pop(0)
                    + " "
                    + remaining_line.pop(0)
                    + " "
                    + remaining_line.pop(0)
                )
            # 16 Data Item 030 Warning/Error Conditions/Target Classification Not needed
            if fspec[15]:
                for j, octet in enumerate(remaining_line):
                    removed_octets += octet + " "
                # If the last bit is 0, stop reading
                if octet[7] == "0":
                    unused_octets = remaining_line[
                        j + 1 :
                    ]  # Store remaining unread octets
                try:
                    remaining_line = unused_octets
                except UnboundLocalError:
                    print(
                        "Not enough octets to process Data Item 030 in line " + str(i)
                    )
            # 17 Data Item 080 Mode 3A Code Confidence Indicator Not needed
            if fspec[16]:
                removed_octets = remaining_line.pop(0) + " " + remaining_line.pop(0)
            # 18 Data Item 100 Mode-C Code and Confidence Indicator Not needed
            if fspec[17]:
                removed_octets = (
                    remaining_line.pop(0)
                    + " "
                    + remaining_line.pop(0)
                    + " "
                    + remaining_line.pop(0)
                    + " "
                    + remaining_line.pop(0)
                )
            # 19 Data Item 110 Height Measured by 3D Radar
            if fspec[18]:
                try:
                    message = remaining_line.pop(0) + " " + remaining_line.pop(0)
                    height = get_height_measured(message)
                    new_csv_line += ";" + str(height)
                except IndexError:
                    new_csv_line += ";N/A"
            elif not fspec[18]:
                new_csv_line += ";N/A"
            # 20 Data Item 120 Radial Doppler Speed Not Needed
            if fspec[19]:
                try:
                    # Primary subfield (first octet)
                    primary_subfield = remaining_line.pop(0)
                    removed_octets = primary_subfield + " "

                    # Check CAL (bit 8) and RDS (bit 7) in the primary subfield
                    CAL = int(primary_subfield[0])  # bit-8
                    RDS = int(primary_subfield[1])  # bit-7
                    FX = int(primary_subfield[7])  # bit-1 (LSB)

                    # If CAL is set, read 2 octets (Subfield #1)
                    if CAL == 1:
                        for _ in range(2):
                            removed_octets += remaining_line.pop(0) + " "

                    # If RDS is set, read 7 octets (Subfield #2)
                    if RDS == 1:
                        for _ in range(7):
                            removed_octets += remaining_line.pop(0) + " "

                    # If FX is set, there may be additional octets
                    if FX == 1:
                        while True:
                            extension_octet = remaining_line.pop(0)
                            removed_octets += extension_octet + " "
                            # Stop reading if the last bit (FX) is 0
                            if extension_octet[7] == "0":
                                print("Last bit is 0, stopping reading")

                except IndexError:
                    print("Not enough octets to process Data Item 120")
            # 21 Data Item 230 Communications / ACAS Capability and Flight Status
            if fspec[20]:
                try:
                    message = remaining_line.pop(0) + " " + remaining_line.pop(0)
                    result = get_comms(message)
                    for key, value in result.items():
                        new_csv_line = new_csv_line + ";" + str(value)
                except IndexError:
                    new_csv_line += ";N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A"
            elif not fspec[20]:
                new_csv_line += ";N/A;N/A;N/A;N/A;N/A;N/A;N/A;N/A"

            csv_lines.append(new_csv_line)
            i = i + 1
        except IndexError:
            print("Not enough octets to process line " + str(i))
    # Write the CSV lines to a file if needed
    with open(output_file, "w") as csv_file:
        csv_file.write("\n".join(csv_lines))
