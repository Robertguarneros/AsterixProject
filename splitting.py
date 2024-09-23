def read_and_save_binary(input_file, output_file):
    try:
        # Open the binary file
        with open(input_file, "rb") as binary_file, open(output_file, "w") as text_file:
            # Read the entire content of the file
            byte = binary_file.read(1)
            while byte:
                # Convert the byte to its binary representation
                # Remove the "0b" prefix and pad with zeros to get 8 bits
                binary_representation = format(ord(byte), "08b")
                #print(binary_representation, end=" ")
                text_file.write(binary_representation + " ")
                # Read the next byte
                byte = binary_file.read(1)

    except FileNotFoundError:
        print(f"File {input_file} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def split_into_lines(input_file, output_file):
    try:
        # Open the input file
        with open(input_file, "r") as text_file:
            # Read the entire content of the file
            content = text_file.read()
            # Split the content into octets (assuming space-separated)
            octets = content.split()

        with open(output_file, "w") as out_file:
            # Process the octets in a loop
            while True:
                try:
                    # Get 1 octet for CAT (the category)
                    cat = octets.pop(0)
                    print(cat)
                    
                    # Get 2 octets for Length (convert them to an integer)
                    length_octet_1 = octets.pop(0)
                    length_octet_2 = octets.pop(0)
                    length = int(length_octet_1 + length_octet_2, 2)  # Interpreting the length in binary
                    print(length)
                    # Calculate the remaining octets (subtracting the 2 length octets and CAT)
                    remaining_length = length - 3

                    # Create a new line combining CAT, Length, and the rest of the octets
                    new_line = cat + " " + length_octet_1 + " " + length_octet_2 + " "

                    # Append the remaining octets according to the length
                    for i in range(remaining_length):
                        new_line += octets.pop(0) + " "
                    
                    # Write the new line to the output file
                    out_file.write(new_line.strip() + "\n")

                except IndexError:
                    # End of file reached or octets exhausted
                    break

    except FileNotFoundError:
        print(f"File {input_file} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


# Example usage:
#read_and_save_binary("assets/test.ast", "output_test.txt")


# Example usage
split_into_lines("output_test.txt", "output_file.txt")
