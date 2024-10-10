# MEASURED POSITION IN POLAR COORDINATES
def decode_040(message):

    # Dividimos el mensaje en cuatro octetos (0,1 = RHO; 2,3 = THETA)
    first_octet = message.split()[0]  
    second_octet = message.split()[1]  
    third_octet = message.split()[2]  
    fourth_octet = message.split()[3]  

    # Concatenamos los primeros dos octetos para obtener el valor de RHO (16 bits)
    rho_bin = first_octet + second_octet
    # Concatenamos los últimos dos octetos para obtener el valor de THETA (16 bits)
    theta_bin = third_octet + fourth_octet

    # Convertimos los binarios a decimal
    RHO = int(rho_bin, 2) * (1 / 256)  # RHO en NM (cada bit es 1/256 NM)
    THETA = int(theta_bin, 2) * (360 / 65536)  # THETA en grados (216 = 65536)

    # Retornamos los valores de RHO y THETA
    return RHO, THETA


message = '00110000 10100111 10111010 00110100'
resultado = decode_040(message)
print(resultado)
