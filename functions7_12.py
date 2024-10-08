def get_data_item_I048_130(bytes):
    byte_string = bytes.replace(" ", "")
    if len(byte_string) < 8:
        raise ValueError("Input must be at least 1 byte long")
    
    # Get the primary subfield (first octet)
    primary_subfield = byte_string[:8]
    
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

    # Extract subfield values based on their presence
    bit_offset = 8  # Start after the first octet (primary subfield)

    # Subfield #1 (SSR Plot Runlength)
    if subfields["SRL"]:
        srl_bits = byte_string[bit_offset:bit_offset + 8]
        srl_value = int(srl_bits, 2) * (360 / 2**13)
        result["SSR Plot Runlength (degrees)"] = srl_value
        bit_offset += 8
    
    # Subfield #2 (Number of received replies for MSSR)
    if subfields["SRR"]:
        srr_bits = byte_string[bit_offset:bit_offset + 8]
        srr_value = int(srr_bits, 2)  # LSB = 1
        result["Number of received replies for MSSR"] = srr_value
        bit_offset += 8
    
    # Subfield #3 (Amplitude of MSSR Reply)
    if subfields["SAM"]:
        sam_bits = byte_string[bit_offset:bit_offset + 8]
        sam_value = int(sam_bits, 2) if sam_bits[0] == '0' else int(sam_bits, 2) - (1 << 8)
        result["Amplitude of MSSR Reply (dBm)"] = sam_value
        bit_offset += 8
    
    # Subfield #4 (Primary Plot Runlength)
    if subfields["PRL"]:
        prl_bits = byte_string[bit_offset:bit_offset + 8]
        prl_value = int(prl_bits, 2) * (360 / 2**13)
        result["Primary Plot Runlength (degrees)"] = prl_value
        bit_offset += 8
    
    # Subfield #5 (Amplitude of Primary Plot)
    if subfields["PAM"]:
        pam_bits = byte_string[bit_offset:bit_offset + 8]
        pam_value = int(pam_bits, 2) if pam_bits[0] == '0' else int(pam_bits, 2) - (1 << 8)
        result["Amplitude of Primary Plot (dBm)"] = pam_value
        bit_offset += 8
    
    # Subfield #6 (Difference in Range between PSR and SSR plot)
    if subfields["RPD"]:
        rpd_bits = byte_string[bit_offset:bit_offset + 8]
        rpd_value = int(rpd_bits, 2) if rpd_bits[0] == '0' else int(rpd_bits, 2) - (1 << 8)
        result["Difference in Range (PSR-SSR) (NM)"] = rpd_value / 256
        bit_offset += 8
    
    # Subfield #7 (Difference in Azimuth between PSR and SSR plot)
    if subfields["APD"]:
        apd_bits = byte_string[bit_offset:bit_offset + 8]
        apd_value = int(apd_bits, 2) if apd_bits[0] == '0' else int(apd_bits, 2) - (1 << 8)
        result["Difference in Azimuth (PSR-SSR) (degrees)"] = apd_value * (360 / 2**14)
        bit_offset += 8
    
    return result

def get_data_item_I048_220(bytes):
    # Data Item I048/220
    bytes = bytes.replace(" ", "")

    # Convert binary string to an integer using base 2
    integer_value = int(bytes, 2)

    # Convert the integer to a hexadecimal string
    hex_value = hex(integer_value)[2:].upper()

    print("TA="+hex_value)

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

def get_data_item_I048_240(bytes_str):
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
    print ("TI="+ascii_result)
    return ascii_result
    

def get_data_item_I048_161(bytes):
    # Data Item I048/161
    bytes = bytes.replace(" ", "")

    # Convert binary string to an integer using base 2
    integer_value = int(bytes, 2)

    print("Track Number="+str(integer_value))

    return integer_value

def get_data_item_I048_042(bytes):
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


bytes130 = "11111110 00011000 00000100 11001001 00000111 00101010 00001010 00000100"
decoded_values = get_data_item_I048_130(bytes130)
for field, value in decoded_values.items():
    print(f"{field}: {value}")

bytes220 = "01001010 00001000 11101011"
get_data_item_I048_220(bytes220)

bytes240 = "01001000 11110101 00110100 11000111 01011000 00100000"
get_data_item_I048_240(bytes240)

bytes161 = "00000111 10000011"
get_data_item_I048_161(bytes161)

bytes042 = "10000000 00000000 11111111 11111111"
x, y = get_data_item_I048_042(bytes042)
print(f"X: {x} NM, Y: {y} NM")

