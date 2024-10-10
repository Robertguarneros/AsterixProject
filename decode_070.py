# MODEL-3/A CODE IN OCTAL REPRESENTATION
def decode_070(message):

     # Dividimos el mensaje en dos octetos
    first_octet_bin = message.split()[0] 
    second_octet_bin = message.split()[1] 

    # Extraemos los bits de control directamente
    V = 'Code not validated' if first_octet_bin[0] == '1' else 'Code Validated'  # Bit 16: Validación (V)
    G = 'Garbled code' if first_octet_bin[1] == '1' else 'Default'  # Bit 15: Código Garbled (G)
    L = 'Mode-3/A code not extracted during the last scan' if first_octet_bin[2] == '1' else 'Mode-3/A code derived from the reply of the transponder'  # Bit 14: Código derivado en la última exploración (L)

    # Extraemos el código Mode-3/A en formato octal de bits 12 a 1 (de A4 a D1)
    A = (int(first_octet_bin[4]) * 4) + (int(first_octet_bin[5]) * 2) + int(first_octet_bin[6])
    B = (int(first_octet_bin[7]) * 4) + (int(second_octet_bin[0]) * 2) + int(second_octet_bin[1])
    C = (int(second_octet_bin[2]) * 4) + (int(second_octet_bin[3]) * 2) + int(second_octet_bin[4])
    D = (int(second_octet_bin[5]) * 4) + (int(second_octet_bin[6]) * 2) + int(second_octet_bin[7])

    # Convertimos el código Mode-3/A en una representación octal
    mode_3a_code = f'{A}{B}{C}{D}'

    # Retornamos los valores de los bits de control y el código octal
    return V, G, L, mode_3a_code



message = '00001000 00000100'
resultado = decode_070(message)
print(resultado)
