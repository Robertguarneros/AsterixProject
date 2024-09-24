import re


def FSPEC(input_file):
    try:
        # Open the binary file and the output file
        with open(input_file, "r") as file:

            line = file.readline()
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




           

    except FileNotFoundError:
        print(f"File {input_file} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

FSPEC("output_file.txt")
