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
    print(message)
        
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
    return hours, minutes, seconds, time

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
            hours, minutes, seconds, time = get_time_of_day(message)
            new_csv_line = new_csv_line+str(time)+";"

        print(new_csv_line)
        i = i+1

        


convert_to_csv("assets/test.ast")