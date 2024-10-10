# DATA SOURCE IDENTIFIER
def decode_010(message):
        
    # Dividimos el mensaje en tres octetos
    first_octet = message.split()[0]  
    second_octet = message.split()[1]  

    # Convertimos los binarios a enteros
    SAC = int(first_octet, 2)  # SAC (System Area Code) en binario a decimal
    SIC = int(second_octet, 2)  # SIC (System Identification Code) en binario a decimal
        
    # Retornamos los valores de SAC y SIC descodificados
    return SAC, SIC


message = '00010100 10000001'
resultado = decode_010(message)
print(resultado)
