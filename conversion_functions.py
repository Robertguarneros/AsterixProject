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


def convert_to_csv(input_file):
    lines = read_and_split_binary(input_file)
    csv_lines = []
    new_csv_line = "NUM;SAC;SIC;TIME;TIME(s);LAT;LON;H;TYP_020;SIM_020;RDP_020;SPI_020;RAB_020;TST_020;ERR_020;XPP_020;ME_020;MI_020;FOE_FRI_020;RHO;THETA;V_070;G_070;MODE 3/A;V_090;G_090;FL;MODE C corrected;SRL_130;SSR_130;SAM_130;PRL_130;PAM_130;RPD_130;APD_130;TA;TI;MCP_ALT;FMS_ALT;BP;VNAV;ALT_HOLD;APP;TARGET_ALT_SOURCE;RA;TTA;GS;TAR;TAS;HDG;IAS;MACH;BAR;IVV;TN;X;Y;GS_KT;HEADING;CNF_170;RAD_170;DOU_170;MAH_170;CDM_170;TRE_170;GHO_170;SUP_170;TCC_170;HEIGHT;COM_230;STAT_230;SI_230;MSCC_230;ARC_230;AIC_230;B1A_230;B1B_230"
    csv_lines.append(new_csv_line)
    i=1
    for line in lines:
        new_csv_line = str(i)+";"
        fspec, remaining_line = get_fspec(line)

        if fspec[0] == True:
            # Data Item 010 SAC, SIC
            message = remaining_line.pop(0)+" "+remaining_line.pop(0)
            sac, sic = get_sac_sic(message)
            new_csv_line = new_csv_line+str(sac)+";"+str(sic)+";"
        if fspec[1] == True:
            # Data Item 140 Time of Day
            message = remaining_line.pop(0)+" "+remaining_line.pop(0)+" "+remaining_line.pop(0)
            time, total_seconds = get_time_of_day(message)
            new_csv_line = new_csv_line+str(time)+";"+str(total_seconds)+";"
        if fspec[2] == True:
            # Data Item 020 Target Report Descriptor
            message = remaining_line
            TYP, SIM, RDP, SPI, RAB, TST, ERR, XPP, ME, MI, FOE_FRI, ADSB_EP, ADSB_VAL, SCN_EP, SCN_VAL, PAI_EP, PAI_VAL, remaining_line = get_target_report_descriptor(message)
            new_csv_line = new_csv_line +";"+ str(TYP)+";"+str(SIM)+";"+str(RDP)+";"+str(SPI)+";"+str(RAB)+";"+str(TST)+";"+str(ERR)+";"+str(XPP)+";"+str(ME)+";"+str(MI)+";"+str(FOE_FRI)

        print(new_csv_line)
        i = i+1

        
# Missing to insert the latitude longitude and height at the position expected in csv

convert_to_csv("assets/test.ast")