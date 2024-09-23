def read_and_split_binary(input_file, output_file):
    try:
        # Open the binary file and the output file
        with open(input_file, "rb") as binary_file, open(output_file, "w") as out_file:
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

                # Write the complete line to the output file
                out_file.write(new_line.strip() + "\n\n")

    except FileNotFoundError:
        print(f"File {input_file} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


# Example usage
read_and_split_binary("assets/test.ast", "output_file.txt")
