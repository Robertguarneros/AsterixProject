import re


def FSPEC(line):

    DataItems = []
    separated_line = re.split(r"\s+", line.strip())

    del separated_line[0:3]
    print(separated_line)
    fspec = ""
    
    for oct in separated_line:

        octet = str(oct)

        fspec = fspec + octet + " "

        if octet[7] == "0":
            break

    print(fspec)
    fspec = fspec.replace(" ", "")
    for i, oct in enumerate(fspec):
        # Check if you are at the 7th position (index 6)
        if i == 6:
            pass  # Skip this position
        elif i == 15:
            pass
        elif i == 23:
            pass
        elif i == 31:
            pass
        else:
            # Your existing logic for other positions
            if str(oct) == "1":
                DataItems.append(True)
            elif str(oct) == "0":
                DataItems.append(False)


    print(DataItems)
    print (len(DataItems))

    return DataItems

FSPEC("00110000 00000000 01000111 11111111 11110111 00000010     00010100    10000001    00111000 01000000 01101101 11100000 00110000 10100111 10111010 00110100 00001000 00000100 00000101 11001000 11111110 00011000 00000100 11001001 00000111 00101010 00001010 00000100 01001010 00001000 11101011 01001000 11110101 00110100 11000111 01011000 00100000 00000011 11001000 01001110 01000010 01110000 10101000 00000000 00000000 01000000 10000000 00011011 10010111 00110011 00100000 00000100 11010110 01010000 11011111 01001001 11100111 00101111 00100000 00010100 00000001 01100000 00000111 10000011 00000111 01000010 10111001 01100010 00000110 00100000 11111101")
