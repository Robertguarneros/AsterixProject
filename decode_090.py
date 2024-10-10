# FLIGHT LEVEL IN BINARY REPRESENTATION
def decode_090(message):

    # Dividimos el mensaje en dos octetos
    first_octet_bin = message.split()[0]  # Primer octeto en binario
    second_octet_bin = message.split()[1]  # Segundo octeto en binario

    # Extraemos los bits de control directamente
    V = 'Code not validated' if first_octet_bin[0] == '1' else 'Code Validated'  # Bit 16: Validación (V)
    G = 'Garbled code' if first_octet_bin[1] == '1' else 'Default'  # Bit 15: Código Garbled (G)

    # Extraemos el nivel de vuelo (bits 14 a 1) como un solo bloque
    flight_level_bin = first_octet_bin[2:] + second_octet_bin  # De bits 14 a 1

    # Convertimos el nivel de vuelo a decimal
    flight_level = int(flight_level_bin, 2) * 0.25  # LSB=1/4 FL

    # Retornamos los valores de los bits de control y el nivel de vuelo
    return V, G, flight_level


message = '00000101 11001000'
resultado = decode_090(message)
print(resultado)
