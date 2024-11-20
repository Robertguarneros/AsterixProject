import csv
import ctypes
import math
import os
import platform
import re
import sys
import webbrowser

import numpy as np
from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QProgressDialog,
    QPushButton,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


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


def geodesic_to_geocentric(lat, lon, alt):
    """
    Converts geodetic coordinates (latitude, longitude, height) to geocentric (x, y, z).
    """

    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    nu = A / np.sqrt(1 - E2 * np.sin(lat_rad) ** 2)

    x = (nu + alt) * np.cos(lat_rad) * np.cos(lon_rad)
    y = (nu + alt) * np.cos(lat_rad) * np.sin(lon_rad)
    z = (nu * (1 - E2) + alt) * np.sin(lat_rad)
    return np.array([x, y, z])


def get_rotation_matrix(lat, lon):
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    return np.array(
        [
            [-np.sin(lon_rad), np.cos(lon_rad), 0],
            [
                -np.sin(lat_rad) * np.cos(lon_rad),
                -np.sin(lat_rad) * np.sin(lon_rad),
                np.cos(lat_rad),
            ],
            [
                np.cos(lat_rad) * np.cos(lon_rad),
                np.cos(lat_rad) * np.sin(lon_rad),
                np.sin(lat_rad),
            ],
        ]
    )


def get_translation_vector(lat, lon, alt):
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    nu = A / np.sqrt(1 - E2 * np.sin(lat_rad) ** 2)
    return np.array(
        [
            [(nu + alt) * np.cos(lat_rad) * np.cos(lon_rad)],
            [(nu + alt) * np.cos(lat_rad) * np.sin(lon_rad)],
            [(nu * (1 - E2) + alt) * np.sin(lat_rad)],
        ]
    )


def geocentric_to_system_cartesian(geocentric_coords):
    geo = {
        "X": geocentric_coords[0],
        "Y": geocentric_coords[1],
        "Z": geocentric_coords[2],
    }
    center = {"Lat": 41.10904, "Lon": 1.226947, "Alt": 3438.954}
    R = get_rotation_matrix(center["Lat"], center["Lon"])
    T = get_translation_vector(center["Lat"], center["Lon"], center["Alt"])

    input_vector = np.array([[geo["X"]], [geo["Y"]], [geo["Z"]]])
    result_vector = R @ (input_vector - T)

    return {
        "X": result_vector[0, 0],
        "Y": result_vector[1, 0],
        "Z": result_vector[2, 0],
    }


def system_cartesian_to_system_stereographical(c):
    class CoordinatesUVH:
        def __init__(self):
            self.U = 0
            self.V = 0
            self.Height = 0

    res = CoordinatesUVH()
    center = {"Lat": 41.10904, "Lon": 1.226947, "Alt": 3438.954}

    lat_rad = np.radians(center["Lat"])

    R_S = (A * (1.0 - E2)) / (1 - E2 * np.sin(lat_rad) ** 2) ** 1.5

    d_xy2 = c["X"] ** 2 + c["Y"] ** 2
    res.Height = np.sqrt(d_xy2 + (c["Z"] + center["Alt"] + R_S) ** 2) - R_S

    k = (2 * R_S) / (2 * R_S + center["Alt"] + c["Z"] + res.Height)
    res.U = k * c["X"]
    res.V = k * c["Y"]

    return {"U": res.U, "V": res.V, "Height": res.Height}


def get_stereographical_from_lat_lon_alt(lat, lon, alt):
    geocentric_coords = geodesic_to_geocentric(lat, lon, alt)
    cartesian_coords = geocentric_to_system_cartesian(geocentric_coords)
    stereographical_coords = system_cartesian_to_system_stereographical(
        cartesian_coords
    )
    return stereographical_coords


def calculate_distance(U1, V1, U2, V2):
    distance = np.sqrt((U1 - U2) ** 2 + (V1 - V2) ** 2) / 1852
    return distance


# Function that processes all the data items in a single line
def convert_to_csv(input_file, output_file, progress_dialog):
    lines = read_and_split_binary(input_file)
    csv_lines = []
    new_csv_line = "NUM;SAC;SIC;TIME;TIME(s);LAT;LON;H;TYP_020;SIM_020;RDP_020;SPI_020;RAB_020;TST_020;ERR_020;XPP_020;ME_020;MI_020;FOE_FRI_020;RHO;THETA;V_070;G_070;MODE 3/A;V_090;G_090;FL;MODE C Corrected Altitude;SRL_130;SSR_130;SAM_130;PRL_130;PAM_130;RPD_130;APD_130;TA;TI;MCP_ALT;FMS_ALT;BP;VNAV;ALT_HOLD;APP;TARGET_ALT_SOURCE;RA;TTA;GS;TAR;TAS;HDG;IAS;MACH;BAR;IVV;TN;X;Y;GS_KT;HEADING;CNF_170;RAD_170;DOU_170;MAH_170;CDM_170;TRE_170;GHO_170;SUP_170;TCC_170;HEIGHT;COM_230;STAT_230;SI_230;MSCC_230;ARC_230;AIC_230;B1A_230;B1B_230"
    csv_lines.append(new_csv_line)
    i = 1
    for line in lines:
        progress_value = int((i / len(lines)) * 100)
        progress_dialog.set_progress(progress_value)
        QApplication.processEvents()
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
    progress_dialog.set_progress(100)
    # Close the dialog when done
    progress_dialog.accept()  # Close the dialog here


class ProgressDialog(QDialog):
    """Dialog to show the progress of CSV loading."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Loading CSV Data")
        self.setFixedSize(300, 100)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(30, 40, 240, 25)

        # Label
        self.label = QLabel("Loading CSV into table, please wait...", self)
        self.label.setAlignment(Qt.AlignCenter)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

    def set_progress(self, value):
        """Updates the progress bar."""
        self.progress_bar.setValue(value)


class ProgressDialog2(QDialog):
    """Dialog to show the progress of CSV loading."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Convert to CSV")
        self.setFixedSize(300, 100)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(30, 40, 240, 25)

        # Label
        self.label = QLabel("Converting Asterix to CSV, please wait...", self)
        self.label.setAlignment(Qt.AlignCenter)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

    def set_progress(self, value):
        """Updates the progress bar."""
        self.progress_bar.setValue(value)


class CSVTableDialog(QDialog):
    """Dialog to show CSV data in a table with filtering capabilities."""

    def __init__(self, csv_file_path, parent=None, progress_dialog=None):
        super().__init__(parent)
        self.setWindowTitle("CSV Data")

        self.aircraft_data_by_time = {}  # Initialize the attribute here
        self.aircraft_list = {}
        self.last_known_time_for_aircraft = {}

        # Create table widget
        self.table_widget = QTableWidget()

        # Lista para almacenar los filtros aplicados
        self.applied_filters = []

        # Campos de entrada para latitudes y longitudes
        self.lat_min_input = QLineEdit()
        self.lat_max_input = QLineEdit()
        self.lon_min_input = QLineEdit()
        self.lon_max_input = QLineEdit()

        self.lat_min_input.setPlaceholderText("Lat Min")
        self.lat_max_input.setPlaceholderText("Lat Max")
        self.lon_min_input.setPlaceholderText("Lon Min")
        self.lon_max_input.setPlaceholderText("Lon Max")

        # Botón para aplicar filtro de área
        self.apply_area_filter_button = QPushButton("Apply Area Filter")
        self.apply_area_filter_button.clicked.connect(self.apply_area_filter)

        # Botón para deshacer el filtro de área
        self.reset_area_filter_button = QPushButton("Reset Area Filter")
        self.reset_area_filter_button.clicked.connect(self.reset_area_filter)

        # Etiqueta para mostrar las coordenadas del filtro activo
        self.active_area_filter_label = QLabel("Active Area Filter: None")

        # Create "Start Simulation" button, hidden by default
        self.start_simulation_button = QPushButton("Start Simulation")
        self.start_simulation_button.setVisible(False)
        self.start_simulation_button.clicked.connect(parent.start_simulation)

        # Add export button
        self.export_button = QPushButton("Export Filtered Data")
        self.export_button.clicked.connect(self.export_filtered_data)

        # Add simulation button
        self.simulation_button = QPushButton("Simulate Filtered Data")
        self.simulation_button.clicked.connect(self.initialize_simulation)

        # Filter options
        self.filter_combobox = QComboBox()
        self.filter_combobox.setEditable(False)  # No se puede editar el texto
        self.filter_combobox.addItem(
            "Active Filters: None"
        )  # Cabecera que mostrará filtros activos
        self.filter_combobox.model().item(0).setEnabled(
            False
        )  # Deshabilitar primera opción (cabecera)

        # Opciones de filtro
        self.filter_combobox.addItem("No Filter")
        self.filter_combobox.addItem("Remove Blancos Puros")
        self.filter_combobox.addItem("Remove Fixed Transponder")
        self.filter_combobox.addItem("Remove On Ground Flights")

        # Botón de aplicar filtros
        self.apply_filter_button = QPushButton("Apply Filter")
        self.apply_filter_button.clicked.connect(self.apply_filters)

        # Filter layout
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(self.filter_combobox)
        filter_layout.addWidget(self.apply_filter_button)

        # Crear ComboBox para columna de búsqueda y QLineEdit para introducir texto
        self.search_column_combobox = QComboBox()
        self.search_column_combobox.setFixedWidth(
            150
        )  # Reducir el tamaño de la caja de texto del buscador
        self.search_column_combobox.addItem(
            "Searcher"
        )  # Texto visible como placeholder
        self.search_column_combobox.model().item(0).setEnabled(
            False
        )  # Deshabilitar este ítem para que no sea seleccionable

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search text")
        self.search_input.setFixedWidth(
            300
        )  # Reducir el tamaño de la caja de texto del buscador
        self.search_input.textChanged.connect(self.apply_search_filter)

        # Crear layout para el buscador y alinearlo a la derecha
        search_layout = QHBoxLayout()
        search_layout.addStretch()  # Asegura que el buscador se alinee a la derecha
        search_layout.addWidget(self.search_column_combobox)
        search_layout.addWidget(self.search_input)

        # Main layout
        layout = QVBoxLayout()
        layout.addLayout(filter_layout)
        layout.addLayout(search_layout)  # Añadir el layout del buscador aquí
        layout.addWidget(self.table_widget)
        layout.addWidget(self.start_simulation_button)
        self.setLayout(layout)

        # Filtros de área en el layout horizontal
        area_filter_layout = QHBoxLayout()
        area_filter_layout.addWidget(QLabel("Latitude Range:"))
        area_filter_layout.addWidget(self.lat_min_input)
        area_filter_layout.addWidget(self.lat_max_input)
        area_filter_layout.addWidget(QLabel("Longitude Range:"))
        area_filter_layout.addWidget(self.lon_min_input)
        area_filter_layout.addWidget(self.lon_max_input)
        area_filter_layout.addWidget(self.apply_area_filter_button)
        area_filter_layout.addWidget(self.reset_area_filter_button)

        # Añadir los layouts al layout principal
        layout.addLayout(area_filter_layout)
        layout.addWidget(self.active_area_filter_label)

        # Sets to track rows hidden by area filter and other filters
        self.area_hidden_rows = set()
        self.other_filters_hidden_rows = set()

        # Add export and simulation button to layout
        expSim_layout = QHBoxLayout()
        expSim_layout.addWidget(self.export_button)
        expSim_layout.addWidget(self.simulation_button)

        # Añadir layout al layout principal
        layout.addLayout(expSim_layout)

        # Load CSV data with a progress dialog
        self.load_csv_data(csv_file_path, progress_dialog)

        # Inicializamos las filas visibles y las que ha ocultado el buscador
        self.currently_visible_rows = set(
            range(self.table_widget.rowCount())
        )  # Todas las filas visibles al inicio
        self.search_hidden_rows = set()  # Filas ocultadas solo por el buscador

        # Populate search column combobox with table headers
        self.populate_search_columns()

        # Ocultar la columna de numeración de filas (índices de fila)
        self.table_widget.verticalHeader().setVisible(False)

        # Allow window to be maximized with a system maximize button
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowMinimizeButtonHint
        )
        self.setWindowModality(Qt.NonModal)  # Para que no bloquee la ventana principal

        # Show the dialog in a normal windowed mode, user can maximize it
        self.showMaximized()

    def populate_search_columns(self):
        """Populate the search column combobox with the table's column headers."""
        for col in range(self.table_widget.columnCount()):
            header_text = self.table_widget.horizontalHeaderItem(col).text()
            self.search_column_combobox.addItem(header_text, col)

    def apply_search_filter(self):
        """Filter rows based on the text in the search input for the selected column."""
        search_text = self.search_input.text().strip().lower()
        selected_column = self.search_column_combobox.currentData()

        # Si no hay ninguna columna seleccionada o si el texto de búsqueda está vacío, no aplicar filtro.
        if selected_column is None or not search_text:
            # Restaurar solo las filas que ocultó el buscador
            for row in self.search_hidden_rows:
                # Mostrar la fila solo si no está oculta por otros filtros
                if (
                    row not in self.other_filters_hidden_rows
                    and row not in self.area_hidden_rows
                ):
                    self.table_widget.setRowHidden(row, False)
            # Limpiar el conjunto de filas ocultadas por el buscador
            self.search_hidden_rows.clear()
            return

        # Filtrar solo en filas actualmente visibles
        new_search_hidden_rows = (
            set()
        )  # Guardamos las filas que ocultaremos en esta búsqueda
        for row in self.currently_visible_rows:
            # Obtener el texto de la celda solo una vez para mejorar el rendimiento
            cell_text = (
                self.table_widget.item(row, selected_column).text().strip().lower()
            )

            if search_text not in cell_text:
                # Ocultamos la fila y la añadimos a las filas ocultadas por esta búsqueda
                self.table_widget.setRowHidden(row, True)
                new_search_hidden_rows.add(row)
            else:
                # Mostramos la fila solo si no está oculta por otros filtros
                if (
                    row in self.search_hidden_rows
                    and row not in self.other_filters_hidden_rows
                    and row not in self.area_hidden_rows
                ):
                    self.table_widget.setRowHidden(row, False)

        # Actualizamos las filas ocultadas por el buscador para esta búsqueda
        self.search_hidden_rows = new_search_hidden_rows

    def export_filtered_data(self):
        """Exports the filtered data to a new CSV file using semicolons as the delimiter."""
        self.search_input.clear()  # Limpiar texto del buscador para q no afecte a lo q exportas
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Filtered Data As",
            "",
            "CSV Files (*.csv);;All Files (*)",
            options=options,
        )

        if file_path:
            with open(file_path, mode="w", newline="") as file:
                writer = csv.writer(file, delimiter=";")  # Use semicolon as delimiter

                # Write headers
                headers = [
                    self.table_widget.horizontalHeaderItem(i).text()
                    for i in range(self.table_widget.columnCount())
                ]
                writer.writerow(headers)

                # Write filtered rows
                for row in range(self.table_widget.rowCount()):
                    if not self.table_widget.isRowHidden(row):
                        row_data = [
                            (
                                self.table_widget.item(row, col).text()
                                if self.table_widget.item(row, col)
                                else ""
                            )
                            for col in range(self.table_widget.columnCount())
                        ]
                        writer.writerow(row_data)

            QMessageBox.information(
                self,
                "Export Successful",
                "Filtered data has been exported successfully.",
            )

        self.parent().hide_play_pause_buttons()

    def initialize_simulation(self):

        # Ventana de progreso
        self.progress_dialog = QProgressDialog(
            "Loading simulation data, please wait...", "Cancel", 0, 100, self
        )
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setValue(0)  # Inicia en 0%
        self.progress_dialog.setMinimumDuration(0)  # Aparece inmediatamente
        self.progress_dialog.setCancelButton(None)  # Deshabilita el botón de cancelar
        self.progress_dialog.setWindowTitle("Loading Data Simulation")
        self.progress_dialog.show()

        headers = [
            self.table_widget.horizontalHeaderItem(i).text()
            for i in range(self.table_widget.columnCount())
        ]

        time_idx = headers.index("TIME(s)")
        lat_idx = headers.index("LAT")
        lon_idx = headers.index("LON")
        ti_idx = headers.index("TI")
        h_idx = headers.index("H")
        heading_idx = headers.index("HEADING")

        # Dictionary to store aircraft data
        self.aircraft_data_by_time = {}
        self.aircraft_list = set()
        self.last_known_time_for_aircraft = (
            {}
        )  # Almacena el último tiempo de cada avión

        total_rows = self.table_widget.rowCount()

        # Loop through each row of the table widget, starting from the first row after the header
        for row_idx in range(1, self.table_widget.rowCount()):  # Skip header
            try:
                if self.table_widget.isRowHidden(row_idx):
                    continue  # Skip hidden rows

                # Retrieve each cell's data for the row
                row_data = [
                    (
                        self.table_widget.item(row_idx, col_idx).text()
                        if self.table_widget.item(row_idx, col_idx)
                        else ""
                    )
                    for col_idx in range(self.table_widget.columnCount())
                ]
                stereographical_coords = get_stereographical_from_lat_lon_alt(
                    float(row_data[lat_idx].replace(",", ".")),
                    float(row_data[lon_idx].replace(",", ".")),
                    float(row_data[h_idx].replace(",", ".")),
                )
                # Create an aircraft info dictionary for the current row
                aircraft_info = {
                    "time": row_data[time_idx],
                    "lat": float(row_data[lat_idx].replace(",", ".")),
                    "lon": float(row_data[lon_idx].replace(",", ".")),
                    "ti": row_data[ti_idx],
                    "h": float(row_data[h_idx].replace(",", ".")),
                    "heading": float(row_data[heading_idx].replace(",", ".")),
                    "U": float(stereographical_coords["U"]),
                    "V": float(stereographical_coords["V"]),
                }

                time = aircraft_info["time"]
                ti = aircraft_info["ti"]
                lat = aircraft_info["lat"]
                lon = aircraft_info["lon"]
                h = aircraft_info["h"]
                heading = aircraft_info["heading"]

                # Verificar que todos los campos sean diferentes de "N/A"
                if (
                    ti != "N/A"
                    and time != "N/A"
                    and lat != "N/A"
                    and lon != "N/A"
                    and h != "N/A"
                    and heading != "N/A"
                ):

                    # Agregar los aviones al grupo de datos por tiempo
                    if time not in self.aircraft_data_by_time:
                        self.aircraft_data_by_time[time] = []
                    self.aircraft_data_by_time[time].append(aircraft_info)

                    # Agregar el avión a la lista de aviones si no está ya añadido
                    if ti not in self.aircraft_list:
                        self.aircraft_list.add(ti)

                    self.last_known_time_for_aircraft[ti] = str(int(time) + 3)

                # Actualizar la barra de progreso
                progress = int(
                    (row_idx / total_rows) * 100
                )  # Calcular el progreso en porcentaje
                self.progress_dialog.setValue(progress)

                # Si el usuario cierra el diálogo, interrumpimos la simulación
                if self.progress_dialog.wasCanceled():
                    break
            except Exception as e:
                print(f"Error processing row {row_idx}: {e}")

        # Store the organized data in the parent for further use
        self.parent().aircraft_data_by_time = self.aircraft_data_by_time
        self.parent().aircraft_list = list(self.aircraft_list)
        self.parent().last_known_time_for_aircraft = self.last_known_time_for_aircraft

        if self.aircraft_data_by_time:
            min_time = int(min(self.aircraft_data_by_time.keys()))
            max_time = int(max(self.aircraft_data_by_time.keys()))
            self.parent().progress_bar.setRange(
                min_time, max_time
            )  # Ajustar rango del slider
            self.parent().progress_bar.setValue(min_time)  # Initial value

        # Cerrar el diálogo de progreso después de cargar los datos
        self.progress_dialog.close()
        self.resize(400, 300)
        self.parent().show_simulation_buttons()

    def load_csv_data(self, csv_file_path, progress_dialog):
        """Loads data from the CSV file and displays it in the table."""
        with open(csv_file_path, newline="") as csvfile:
            reader = csv.reader(csvfile, delimiter=";")  # Specify ';' as the delimiter
            data = list(reader)
            total_rows = len(data)

            if data:
                # Set row and column count
                self.table_widget.setRowCount(total_rows - 1)  # Exclude header
                self.table_widget.setColumnCount(
                    len(data[0])
                )  # Use first row to set column count

                # Set headers
                headers = data[0]
                self.table_widget.setHorizontalHeaderLabels(headers)

                # Populate table with data and update progress dialog
                for row_idx, row_data in enumerate(data[1:]):  # Skip header
                    try:
                        for col_idx, cell_data in enumerate(row_data):
                            self.table_widget.setItem(
                                row_idx, col_idx, QTableWidgetItem(cell_data)
                            )

                        # Update progress dialog
                        progress_value = int((row_idx / total_rows) * 100)
                        if progress_dialog:
                            progress_dialog.set_progress(progress_value)
                        QApplication.processEvents()
                    except Exception as e:
                        print(f"Error loading row {row_idx}: {e}")
                # Resize columns to fit content
                self.table_widget.resizeColumnsToContents()

                # Resize columns to fit content
                self.table_widget.horizontalHeader().setSectionResizeMode(
                    QHeaderView.Interactive
                )

            self.parent().hide_simulation_buttons()

        # Set progress to 100% when done
        if progress_dialog:
            progress_dialog.set_progress(100)
            # Close the dialog when done
            progress_dialog.accept()  # Close the dialog here

    def apply_filters(self):
        """Applies filters based on the selected option in the combobox."""

        selected_filter = self.filter_combobox.currentText()
        self.search_input.clear()  # Limpiar texto del buscador al aplicar filtros

        if "Active Filters" in selected_filter:
            return

        if selected_filter == "Remove Blancos Puros":
            self.filter_blancos_puros()
        elif selected_filter == "Remove Fixed Transponder":
            self.filter_fixed_transponder()
        elif selected_filter == "Remove On Ground Flights":
            self.filter_on_ground()
        elif selected_filter == "No Filter":
            self.reset_other_filters()

        if (
            selected_filter not in self.applied_filters
            and selected_filter != "No Filter"
        ):
            self.applied_filters.append(selected_filter)

        self.update_active_filters_label()
        self.filter_combobox.setCurrentIndex(0)

    def update_active_filters_label(self):
        """Updates the combobox header to show active filters."""
        if not self.applied_filters:
            header_text = "Active Filters: None"
        else:
            header_text = f"Active Filters: {', '.join(self.applied_filters)}"

        # Cambiar el texto de la cabecera en el primer elemento del QComboBox
        self.filter_combobox.setItemText(0, header_text)

    def filter_blancos_puros(self):
        detection_type_col_idx = 8  # Índice de la columna de tipo de detección
        for row in range(self.table_widget.rowCount()):
            if row in self.currently_visible_rows:
                detection_type = self.table_widget.item(
                    row, detection_type_col_idx
                ).text()
                # Si "ModeS" no está en el tipo de detección, se oculta la fila
                if "ModeS" not in detection_type:
                    self.table_widget.setRowHidden(row, True)  # Ocultar fila
                    self.other_filters_hidden_rows.add(
                        row
                    )  # Añadir a las filas ocultas
                else:
                    self.table_widget.setRowHidden(row, False)  # Mostrar fila
                    self.other_filters_hidden_rows.discard(
                        row
                    )  # Eliminar de las filas ocultas

        # Después de aplicar el filtro, actualizamos la visibilidad de las filas
        self.update_row_visibility()

    def filter_fixed_transponder(self):
        for row in range(self.table_widget.rowCount()):
            transponder_value = self.table_widget.item(row, 23).text()
            if transponder_value == "7777":
                self.other_filters_hidden_rows.add(row)
            else:
                self.other_filters_hidden_rows.discard(row)

        self.update_row_visibility()

    def filter_on_ground(self):
        ground_status_col_idx = 70
        filter_texts = [
            "No alert, no SPI, aircraft on ground",
            "N/A",
            "Not assigned",
            "Alert, no SPI, aircraft on ground",
            "Unknow",
        ]

        for row in range(self.table_widget.rowCount()):
            item = self.table_widget.item(row, ground_status_col_idx)
            if item and item.text() in filter_texts:
                self.other_filters_hidden_rows.add(row)
            else:
                self.other_filters_hidden_rows.discard(row)

        self.update_row_visibility()

    def update_row_visibility(self):
        """Updates visibility of rows based on area and other filter sets, and refreshes the table."""
        for row in range(self.table_widget.rowCount()):
            if row in self.area_hidden_rows or row in self.other_filters_hidden_rows:
                self.table_widget.setRowHidden(row, True)
            else:
                self.table_widget.setRowHidden(row, False)
        # Force a UI update to reflect changes immediately
        QApplication.processEvents()

    def reset_other_filters(self):
        """Resets only the non-area filters and updates the table visibility."""
        self.other_filters_hidden_rows.clear()
        self.update_row_visibility()
        self.applied_filters.clear()
        self.update_active_filters_label()

    def apply_area_filter(self):
        """Applies an area filter based on latitude and longitude range inputs."""
        self.search_input.clear()  # Limpiar texto del buscador al aplicar filtros

        try:
            # Get the latitude and longitude range from the input fields
            lat_min = float(self.lat_min_input.text().replace(",", "."))
            lat_max = float(self.lat_max_input.text().replace(",", "."))
            lon_min = float(self.lon_min_input.text().replace(",", "."))
            lon_max = float(self.lon_max_input.text().replace(",", "."))
        except ValueError:
            QMessageBox.warning(
                self,
                "Input Error",
                "Please enter valid numeric values for the coordinates.",
            )
            return  # Exit the function if the input is invalid

        # Limpiar el conjunto de filas ocultadas solo por el filtro de área
        self.area_hidden_rows.clear()

        # Aplicar el filtro de área a las filas visibles
        for row in range(self.table_widget.rowCount()):
            try:
                # Usar índices fijos para las columnas de latitud y longitud
                lat_item = self.table_widget.item(row, 5)
                lon_item = self.table_widget.item(row, 6)

                if lat_item and lon_item:
                    lat = float(lat_item.text().replace(",", "."))
                    lon = float(lon_item.text().replace(",", "."))

                    # Verificar si las coordenadas están dentro del rango especificado
                    if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                        # Solo mostrar la fila si no está oculta por otros filtros
                        if (
                            row not in self.other_filters_hidden_rows
                            and row not in self.search_hidden_rows
                        ):
                            self.table_widget.setRowHidden(row, False)
                    else:
                        # Ocultar la fila y agregarla a las ocultadas por el filtro de área
                        self.table_widget.setRowHidden(row, True)
                        self.area_hidden_rows.add(row)
                else:
                    # Ocultar filas con latitud/longitud faltante y agregar a las filas ocultas por área
                    self.table_widget.setRowHidden(row, True)
                    self.area_hidden_rows.add(row)

            except ValueError:
                # Si ocurre un error de conversión a float, ocultar la fila y agregar a las ocultas por área
                self.table_widget.setRowHidden(row, True)
                self.area_hidden_rows.add(row)

        # Actualizar la etiqueta de filtro de área activo
        self.active_area_filter_label.setText(
            f"<b>Active Area Filter:</b><br>"
            f"  • <b>Latitude Range:</b> Min {lat_min}° - Max {lat_max}°<br>"
            f"  • <b>Longitude Range:</b> Min {lon_min}° - Max {lon_max}°"
        )

    def reset_area_filter(self):
        """Resets only the area filter and updates the table visibility."""
        # Limpiar el conjunto de filas ocultadas solo por el filtro de área
        self.search_input.clear()  # Limpiar texto del buscador al aplicar filtros
        self.area_hidden_rows.clear()

        # Restaurar solo las filas ocultadas por el filtro de área sin afectar a las filas de otros filtros
        for row in range(self.table_widget.rowCount()):
            if (
                row not in self.other_filters_hidden_rows
                and row not in self.search_hidden_rows
            ):
                self.table_widget.setRowHidden(row, False)

        # Restablecer los campos de entrada y la etiqueta de filtro de área activo
        self.active_area_filter_label.setText("Active Area Filter: None")
        self.lat_min_input.clear()
        self.lat_max_input.clear()
        self.lon_min_input.clear()
        self.lon_max_input.clear()


def resource_path(relative_path):
    """Get the absolute path to a resource, considering PyInstaller's bundling."""
    if hasattr(sys, "_MEIPASS"):
        # Running as a bundled executable
        return os.path.join(sys._MEIPASS, relative_path)
    # Running as a script
    return os.path.join(os.path.abspath("."), relative_path)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asterix Decoder")

        self.aircraft_data_by_time = {}
        self.selected_speed = 1  # Store selected speed; default is 1x
        self.selected_tis = {}

        # Create a central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Set App Icon not necessary when building the executable
        if platform.system() == "Windows":
            myappid = "mycompany.myproduct.subproduct.version"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        # This allows us to set the icon for all the title bars and popups
        icon_path = os.path.join(
            os.path.dirname(__file__), "assets", "logo_eurocontrol.png"
        )
        self.setWindowIcon(QIcon(icon_path))

        # Create main menu
        main_menu = self.menuBar()

        # Create submenu for conversion
        conversion_menu = main_menu.addMenu("Conversion")
        convert_to_csv_action = QAction("Convert Asterix to CSV", self)
        convert_to_csv_action.triggered.connect(self.convert_to_csv_button)
        conversion_menu.addAction(convert_to_csv_action)
        # Add action to load and show CSV data
        load_csv_action = QAction("Load and Show CSV", self)
        load_csv_action.triggered.connect(self.open_csv_table)
        conversion_menu.addAction(load_csv_action)

        # Create submenu for help
        help_menu = main_menu.addMenu("Help")
        help_menu.addAction("Manual", self.open_manual)
        help_menu.addAction("About", self.about_button)

        # Add map
        self.web_view = QWebEngineView()

        # Load the custom Leaflet map HTML file
        html_path = resource_path("map.html")
        self.web_view.setUrl(QUrl.fromLocalFile(os.path.abspath(html_path)))

        # Timer for simulation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)

        # Create a layout for the central widget
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.web_view)

        self.distance_layout = QVBoxLayout()
        self.distance_input = QHBoxLayout()

        # Label and input for Aircraft 1
        self.distance_input.addWidget(
            QLabel("TI Aircraft 1:")
        )  # Label for TI Aircraft 1
        self.ti1_input = QLineEdit()  # Input field for TI Aircraft 1
        self.ti1_input.setPlaceholderText("Enter TI of Aircraft 1")
        self.distance_input.addWidget(self.ti1_input)

        # Label and input for Aircraft 2
        self.distance_input.addWidget(
            QLabel("TI Aircraft 2:")
        )  # Label for TI Aircraft 2
        self.ti2_input = QLineEdit()  # Input field for TI Aircraft 2
        self.ti2_input.setPlaceholderText("Enter TI of Aircraft 2")
        self.distance_input.addWidget(self.ti2_input)

        # Button to calculate the distance
        self.calculate_distance_button = QPushButton("Calculate Distance")
        self.calculate_distance_button.setFixedWidth(500)
        self.calculate_distance_button.clicked.connect(
            self.calculate_distance_between_aircraft
        )
        self.distance_input.addWidget(self.calculate_distance_button)

        self.distance_layout.addLayout(self.distance_input)
        for i in range(self.distance_input.count()):
            self.distance_input.itemAt(i).widget().setVisible(False)

        # Table for displaying distances
        self.distance_table = QTableWidget()
        self.distance_table.setRowCount(3)
        self.distance_table.setColumnCount(
            5
        )  # Columns: TI, Latitude, Longitude, Altitude, Distance
        self.distance_table.setHorizontalHeaderLabels(
            ["TI", "Latitude (°)", "Longitude (°)", "Altitude (m)", "Distance (NM)"]
        )
        self.distance_table.setVisible(False)  # Initially hidde
        self.distance_table.verticalHeader().setVisible(False)

        row_height = self.distance_table.rowHeight(0)  # Get the height of one row
        total_height = (
            3 * row_height - 7
        )  # Calculate the total height based on the rows
        column_width = 160  # Definir un ancho común para todas las columnas

        header = self.distance_table.horizontalHeader()
        for col in range(self.distance_table.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.Stretch)

        self.distance_table.setFixedHeight(total_height)

        # Apply bold font to the header
        header_font = QFont()
        header_font.setBold(True)
        for col in range(self.distance_table.columnCount()):
            self.distance_table.horizontalHeaderItem(col).setFont(header_font)

        self.distance_layout.addWidget(self.distance_table)

        # Message labels below the table
        self.message_label1 = QLabel("")  # First message label
        self.message_label1.setStyleSheet("color: red;")  # Red color for warnings
        self.message_label1.setMaximumHeight(37)
        self.message_label1.setVisible(False)  # Initially hidden
        self.distance_layout.addWidget(self.message_label1)

        self.message_label2 = QLabel("")  # Second message label
        self.message_label2.setStyleSheet("color: red;")  # Red color for warnings
        self.message_label2.setMaximumHeight(37)
        self.message_label2.setVisible(False)  # Initially hidden
        self.distance_layout.addWidget(self.message_label2)

        # Button to undo the selection
        self.undo_selection_button = QPushButton("Undo Selection")
        self.undo_selection_button.clicked.connect(self.undo_selection)
        self.undo_selection_button.setVisible(False)  # Initially hidden
        self.distance_layout.addWidget(self.undo_selection_button)

        layout.addLayout(self.distance_layout)

        self.control_layout = QHBoxLayout()

        # Create a single button for Play/Pause functionality
        self.play_pause_button = QPushButton()
        self.play_pause_button.setText("Play")  # Set initial text to "Play"
        self.play_pause_button.clicked.connect(self.toggle_simulation)
        self.control_layout.addWidget(
            self.play_pause_button
        )  # Add the button to the layout

        # Create a single button for Play/Pause functionality
        self.reset_button = QPushButton()
        self.reset_button.setText("Reset")  # Set initial text to "Play"
        self.reset_button.clicked.connect(self.reset_simulation)
        self.control_layout.addWidget(self.reset_button)  # Add the button to the layout

        # Create a button for Speed selection
        self.speed_button = QPushButton("Speed")
        self.speed_button.setMenu(self.create_speed_menu())
        self.control_layout.addWidget(self.speed_button)  # Add the button to the layout

        self.time_label = QLabel(" ", self)  # Inicializar el label con el tiempo en 0
        self.control_layout.addWidget(self.time_label)

        # Add a progress bar for the simulation
        self.progress_bar = QSlider(Qt.Horizontal)
        self.progress_bar.valueChanged.connect(self.seek_simulation)
        self.control_layout.addWidget(self.progress_bar)

        layout.addLayout(self.control_layout)
        for i in range(self.control_layout.count()):
            self.control_layout.itemAt(i).widget().setVisible(False)

    def open_manual(self):
        pdf_path = resource_path("UserManual.pdf")
        if os.path.exists(pdf_path):
            webbrowser.open_new(pdf_path)
        else:
            QMessageBox.information(
                self, "File not Found", "The manual is not in the expected location."
            )

    def undo_selection(self):
        self.distance_table.setVisible(False)
        self.undo_selection_button.setVisible(False)
        self.selected_tis = {}
        self.ti1_input.clear()
        self.ti2_input.clear()
        self.message_label1.setText("")
        self.message_label1.setVisible(False)
        self.message_label2.setText("")
        self.message_label2.setVisible(False)

    def calculate_distance_between_aircraft(self):
        """Calculate the distance between two aircraft based on their TIs."""
        ti1 = self.ti1_input.text().strip()
        ti2 = self.ti2_input.text().strip()

        # Check if both TIs are entered
        if not ti1 or not ti2:
            QMessageBox.warning(self, "Input Error", "Please enter both TI values.")
            return

        # Ensure the TIs are not the same
        if ti1 == ti2:
            QMessageBox.warning(
                self, "Input Error", "Please enter two different aircrafts."
            )
            return

        # Verify that both TIs exist in the data
        if ti1 not in self.aircraft_list or ti2 not in self.aircraft_list:
            QMessageBox.warning(
                self, "Input Error", "One or both TIs do not exist in the data."
            )
            return

        self.selected_tis = (ti1, ti2)

        # Clear aircraft from the map view
        self.web_view.page().runJavaScript(r"clearAircraft()")

        # Get data for each aircraft
        aircraft1_data = self.update_aircraft_positions_before_current_time(ti1)
        aircraft2_data = self.update_aircraft_positions_before_current_time(ti2)

        # Prepare the table to display results
        self.distance_table.setRowCount(2)
        self.distance_table.setVisible(True)
        self.undo_selection_button.setVisible(True)

        # Update row 1 (aircraft 1)
        self.update_table_row(0, ti1, aircraft1_data)

        # Update row 2 (aircraft 2)
        self.update_table_row(1, ti2, aircraft2_data)

        # Calculate distance if both data points exist
        distance = None
        if aircraft1_data and aircraft2_data:
            distance = self.calculate_dynamic_distance(aircraft1_data, aircraft2_data)

        # Update the distance column (a single cell spanning both rows)
        self.update_distance_cell(distance)

    def update_table_row(self, row, ti, aircraft_data):
        """Helper function to update a row in the distance table."""
        if aircraft_data:
            lat, lon, alt = (
                aircraft_data["lat"],
                aircraft_data["lon"],
                aircraft_data["h"],
            )
        else:
            lat, lon, alt = "N/A", "N/A", "N/A"

        # Update the cells in the row
        self.distance_table.setItem(row, 0, QTableWidgetItem(ti))
        self.distance_table.setItem(row, 1, QTableWidgetItem(str(lat)))
        self.distance_table.setItem(row, 2, QTableWidgetItem(str(lon)))
        self.distance_table.setItem(row, 3, QTableWidgetItem(str(alt)))

        # Ensure the cells are read-only
        for col in range(4):
            item = self.distance_table.item(row, col)
            item.setTextAlignment(Qt.AlignCenter)  # Center-align text
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def update_distance_cell(self, distance):
        """Update the combined cell for distance in the table."""
        self.distance_table.setSpan(
            0, 4, 2, 1
        )  # Merge the cell in column 4 for both rows
        distance_text = f"{distance:.2f}" if distance is not None else "N/A"

        # Create the table widget item
        distance_item = QTableWidgetItem(distance_text)
        distance_item.setTextAlignment(Qt.AlignCenter)
        distance_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        font = QFont()
        font.setPointSize(12)
        distance_item.setFont(font)

        # Set the item in the table
        self.distance_table.setItem(0, 4, distance_item)

    def show_simulation_buttons(self):
        """Shows the Play/Pause button once the simulation is initialized."""
        for i in range(self.control_layout.count()):
            self.control_layout.itemAt(i).widget().setVisible(True)
        for i in range(self.distance_input.count()):
            self.distance_input.itemAt(i).widget().setVisible(True)

    def hide_simulation_buttons(self):
        """Shows the Play/Pause button once the simulation is initialized."""
        for i in range(self.control_layout.count()):
            self.control_layout.itemAt(i).widget().setVisible(False)
        for i in range(self.distance_input.count()):
            self.distance_input.itemAt(i).widget().setVisible(False)

    def seek_simulation(self, value):
        """Searches for a specific time in the simulation based on the slider value."""
        self.current_time = value
        if self.current_time == int(min(self.aircraft_data_by_time.keys())):
            self.web_view.page().runJavaScript(r"clearAircraft()")

        self.time_label.setText(self.seconds_to_hhmmss(value))

    def update_aircraft_positions_before_current_time(self, aircraft):
        """Updates the aircraft's position to the last known point before the current_time."""
        all_times = sorted(map(int, self.aircraft_data_by_time.keys()))

        last_position = None

        for time in reversed(all_times):
            if time < self.current_time:
                aircraft_by_time = self.aircraft_data_by_time.get(str(time), [])
                for a in aircraft_by_time:
                    if a["ti"] == aircraft:
                        last_position = a
                        break
            if last_position is not None:
                break

        last_known_time = int(self.last_known_time_for_aircraft.get(aircraft, -1))

        if last_position and self.current_time <= last_known_time:
            self.update_aircraft_on_map(aircraft, last_position)
            return last_position

        else:
            # If no known position exists, the aircraft is removed from the view
            self.web_view.page().runJavaScript(f"removeAircraft('{aircraft}');")
            return

    def create_speed_menu(self):
        speed_menu = QMenu(self)
        speed_group = QActionGroup(self)  # Create an action group for the speed options

        # Define speed options
        speeds = [
            ("x0.5", 0.5),
            ("x1", 1),
            ("x2", 2),
            ("x4", 4),
            ("x8", 8),
            ("x16", 16),
            ("x32", 32),
            ("x50", 50),
        ]

        for label, value in speeds:
            action = QAction(label, self, checkable=True)
            action.setChecked(value == self.selected_speed)  # Check the selected speed
            action.triggered.connect(
                lambda checked, v=value: self.set_speed(v)
            )  # Bind speed setting
            speed_group.addAction(action)  # Add to the action group
            speed_menu.addAction(action)

        return speed_menu

    def set_speed(self, speed):
        """Sets the selected speed for the simulation."""
        self.selected_speed = speed  # Update the stored speed

        # Update the speed button text to reflect the current selection
        self.speed_button.setText(f"Speed: {speed}x")

        # Optionally, update the simulation timer interval if running
        if self.timer.isActive():
            self.timer.stop()
            interval = int(1000 / self.selected_speed)
            self.timer.start(interval)

    def reset_simulation(self):
        self.current_time = int(min(self.aircraft_data_by_time.keys()))
        self.current_index = 0  # Reset the index
        self.time_label.setText(self.seconds_to_hhmmss(self.current_time))
        self.progress_bar.setValue(self.current_time)  # Initial value

        self.web_view.page().runJavaScript(r"clearAircraft()")

    def toggle_simulation(self):
        """Handles both starting and pausing the simulation."""
        if not self.timer.isActive():
            # Start or resume the simulation
            self.start_simulation()
        else:
            # Pause the simulation
            self.toggle_pause()

    def seconds_to_hhmmss(self, seconds):
        """Convert seconds to hh:mm:ss format."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
        return f"{hours:02}:{minutes:02}:{remaining_seconds:02}"

    def start_simulation(self):
        """Starts the simulation by initializing the timer."""
        if not self.aircraft_data_by_time:
            print("Error: No aircraft data available to start the simulation.")
            return

        # Initialize the current_time with the first time in the dataset
        if not hasattr(self, "current_time") or self.current_time is None:
            self.current_time = int(min(self.aircraft_data_by_time.keys()))
        else:
            # No reset of current_time, continue from where it left off
            self.update_simulation()  # Start the first update manually

        if not self.timer.isActive():
            # Start the timer only if it is not already active
            interval = int(1000 / self.selected_speed)
            self.timer.start(interval)
        # Change the button text and icon to "Pause"
        self.play_pause_button.setText("Pause")

    def toggle_pause(self):
        """Toggles between pausing and resuming the simulation."""
        if self.timer.isActive():
            self.timer.stop()
            self.play_pause_button.setText("Play")
        else:
            interval = int(1000 / self.selected_speed)
            self.timer.start(interval)
            self.play_pause_button.setText("Pause")

    def update_simulation(self):
        """Updates the positions of the aircraft every second of the simulation."""
        current_time_str = str(self.current_time)

        if self.selected_tis:
            # If there are selected TIs, only update those aircraft
            ti1, ti2 = self.selected_tis

            # Get data for the selected aircraft
            aircraft1_data = self.update_aircraft_positions_before_current_time(ti1)
            aircraft2_data = self.update_aircraft_positions_before_current_time(ti2)

            if aircraft1_data:
                self.message_label1.setText(
                    ""
                )  # Clear the message if everything is fine
                self.message_label1.setVisible(False)
            else:
                self.message_label1.setText(f"Aircraft {ti1} is out of bounds.")
                self.message_label1.setVisible(True)

            if aircraft2_data:
                self.message_label2.setText(
                    ""
                )  # Clear the message if everything is fine
                self.message_label2.setVisible(False)
            else:
                self.message_label2.setText(f"Aircraft {ti2} is out of bounds.")
                self.message_label2.setVisible(True)

            # Update the positions of the selected aircraft
            self.update_table_row(0, ti1, aircraft1_data)
            self.update_table_row(1, ti2, aircraft2_data)

            # Calculate distance and update the table
            distance = self.calculate_dynamic_distance(aircraft1_data, aircraft2_data)
            self.update_distance_cell(distance)

        else:
            # Original logic if no aircraft are selected
            if current_time_str in self.aircraft_data_by_time:
                aircraft_list = self.aircraft_data_by_time[current_time_str]
                for aircraft in aircraft_list:
                    ti = aircraft["ti"]
                    self.update_aircraft_on_map(ti, aircraft)

                for aircraft in self.aircraft_list:
                    # Check if the aircraft is not in the current_time_str
                    if not any(a["ti"] == aircraft for a in aircraft_list):
                        self.update_aircraft_positions_before_current_time(aircraft)

        # Update time label and progress bar
        self.time_label.setText(self.seconds_to_hhmmss(self.current_time))
        self.progress_bar.setValue(self.current_time)

        # Increment the time and check for the end of the simulation
        self.current_time += 1
        if self.current_time > int(max(self.aircraft_data_by_time.keys())):
            self.timer.stop()
            QMessageBox.information(
                self, "Simulation Ended", "The simulation has completed."
            )
            self.reset_simulation()
            self.play_pause_button.setText("Play")
        else:
            # Adjust the interval according to the selected speed
            interval = int(1000 / self.selected_speed)
            self.timer.start(interval)

    def update_aircraft_on_map(self, ti, aircraft_data):
        """Helper function to update a specific aircraft on the map."""
        try:
            latitude = aircraft_data["lat"]
            longitude = aircraft_data["lon"]
            altitude = aircraft_data["h"]
            heading = aircraft_data["heading"]

            self.web_view.page().runJavaScript(
                f"updateAircraft('{ti}', {latitude}, {longitude}, {altitude}, {heading});"
            )
        except Exception as e:
            print(f"Error updating aircraft: {e}")

    def calculate_dynamic_distance(self, aircraft1_data, aircraft2_data):
        """Calculate the 3D distance between two aircraft."""
        distance = None
        if aircraft1_data and aircraft2_data:
            u1, v1 = aircraft1_data["U"], aircraft1_data["V"]
            u2, v2 = aircraft2_data["U"], aircraft2_data["V"]

            # Fórmula de distancia en 3D
            distance = calculate_distance(u1, v1, u2, v2)
        return distance

    def open_csv_table(self):
        """Opens a file dialog to select a CSV file and shows it in a table."""
        csv_file_path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )

        if csv_file_path:
            # Show progress dialog during the loading
            progress_dialog = ProgressDialog(self)
            progress_dialog.show()

            # Show CSV table with data
            dialog = CSVTableDialog(csv_file_path, self, progress_dialog)
            dialog.show()

    def convert_to_csv_button(self):
        """Opens a file dialog to select a CSV file and shows it in a table."""
        input_file_path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "Asterix (*.ast);;All Files (*)"
        )
        if input_file_path == "":
            return
        csv_file_path, _ = QFileDialog.getSaveFileName(
            self, "Save as", "", "CSV (*.csv);;All Files (*)"
        )
        if csv_file_path == "":
            return

        QMessageBox.information(
            self,
            "Conversion Started",
            "The conversion process has started. This may take a while.",
        )

        # Show progress dialog during the loading
        progress_dialog2 = ProgressDialog2(self)
        progress_dialog2.show()

        convert_to_csv(input_file_path, csv_file_path, progress_dialog2)

        QMessageBox.information(
            self, "Conversion Successful", "The file has been converted successfully."
        )

        if csv_file_path:
            # Show progress dialog during the loading
            progress_dialog = ProgressDialog(self)
            progress_dialog.show()

            # Show CSV table with data
            dialog = CSVTableDialog(csv_file_path, self, progress_dialog)
            dialog.show()

    def about_button(self):
        """Shows an About dialog with information about the application."""
        QMessageBox.about(
            self,
            "About Asterix Decoder",
            "Asterix Decoder is a tool to convert, visualize and simulate ASTERIX data.\n\n"
            "Created by:\n\nRoberto Guarneros\nAngela Nuñez\nDavid Garcia\n\n"
            "Version: 1.0\n",
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.showMaximized()
    sys.exit(app.exec_())
