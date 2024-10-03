
def get_data_item_I048_220(bytes):
    # Data Item I048/220
    bytes = bytes.replace(" ", "")

    # Convert binary string to an integer using base 2
    integer_value = int(bytes, 2)

    # Convert the integer to a hexadecimal string
    hex_value = hex(integer_value)[2:].upper()

    print(hex_value)

    return {"TA="+hex_value}



bytes = "01001010 00001000 11101011"
get_data_item_I048_220(bytes)