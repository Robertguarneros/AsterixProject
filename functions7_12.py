
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