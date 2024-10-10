# TIME OF DAY
def decode_140(message):

    # Dividimos el mensaje en tres octetos
    first_octet = message.split()[0]  
    second_octet = message.split()[1]  
    third_octet = message.split()[2]  

    # Concatenamos los tres octetos para obtener el valor en binario de 24 bits
    time_of_day_bin = first_octet + second_octet + third_octet

    # Convertimos el binario a decimal
    time_of_day = int(time_of_day_bin, 2)

    # Convertimos de unidades de 1/128 segundos a segundos reales
    total_seconds = time_of_day / 128

    # Calculamos horas, minutos y segundos
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = total_seconds % 60

    TIME = f'{hours:02}:{minutes:02}:{seconds:06.3f}'

    # Retornamos los valores calculados
    return hours, minutes, seconds, TIME

# Ejemplo de uso
message = '00111000 01000000 01101101'
resultado = decode_140(message)
print(resultado)






