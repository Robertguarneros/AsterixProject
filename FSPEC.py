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

with open("output_file.txt", "r") as file:
    line = file.readline()  
    FSPEC(line) 