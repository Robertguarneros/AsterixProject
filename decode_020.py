# TARGET REPORT DESCRIPTOR
def decode_020(message):

    TYP = SIM = RDP = SPI = RAB = TST = ERR = XPP = ME = MI = FOE_FRI = ADSB_EP = ADSB_VAL = SCN_EP = SCN_VAL = PAI_EP = PAI_VAL = None

    # Primer octeto del mensaje que representa el Target Report Descriptor
    first_octet = message.split()[0]  # Tomamos el primer octeto

    # Extraemos los bits según la estructura dada
    typ = first_octet[:3]  # Bits 8/6 (TYP)
    sim = first_octet[3]   # Bit 5 (SIM)
    rdp = first_octet[4]   # Bit 4 (RDP)
    spi = first_octet[5]   # Bit 3 (SPI)
    rab = first_octet[6]   # Bit 2 (RAB)
    FX1 = first_octet[7]    # Bit 1 (FX del primer octeto)

    # Interpretar los valores de TYP
    typ_meaning = {
        '000': "No detection",
        '001': "Single PSR detection",
        '010': "Single SSR detection",
        '011': "SSR + PSR detection",
        '100': "Single ModeS All-Call",
        '101': "Single ModeS Roll-Call",
        '110': "ModeS All-Call + PSR",
        '111': "ModeS Roll-Call + PSR"
    }

        
    # Guardar los resultados del primer octeto en el diccionario
    TYP = typ_meaning.get(typ, "Unknown Detection Type") # Detection type
    SIM = 'Simulated target report' if sim == '1' else 'Actual target report' # Target report
    RDP = 'RDP Chain 2' if rdp == '1' else 'RDP Chain 1' # Report from RDP
    SPI = 'Presence of SPI' if spi == '1' else 'Absence of SPI' # Special Position Identification
    RAB = 'Report from field monitor (fixed transponder)' if rab == '1' else 'Report from aircraft transponder' # Report from

    if FX1 == '1': 
        
        second_octet = message.split()[1]  # Tomamos el segundo octeto

        # Decodificar la extensión
        tst = second_octet[0]  # Bit 8 (TST)
        err = second_octet[1]  # Bit 7 (ERR)
        xpp = second_octet[2]  # Bit 6 (XPP)
        me = second_octet[3]    # Bit 5 (ME)
        mi = second_octet[4]    # Bit 4 (MI)
        foe_fri = second_octet[5:6]  # Bits 3/2 (FOE/FRI)
        FX2 = second_octet[7]         # Bit 1 (FX del segundo octeto)

        # Interpretar los valores de FOE/FRI
        foe_fri_meaning = {
        '00': "No Mode 4 interrogation",
        '01': "Friendly target",
        '10': "Unknown target",
        '11': "No reply"
        }

        # Guardar los resultados del segundo octeto en el diccionario
        TST = 'Test target report' if tst == '1' else 'Real target report' # Target report
        ERR = 'Extended Range present' if err == '1' else 'No Extended Range' # Extended Range
        XPP = 'X-Pulse present' if xpp == '1' else 'No X-Pulse present' # X-Pulse present
        ME = 'Military emergency' if me == '1' else 'No military emergency' # Military emergency
        MI = 'Military identification' if mi == '1' else 'No military identification' # Military identification
        FOE_FRI = foe_fri_meaning.get(foe_fri, "err. FOE/FRI")

        if FX2 == '1': 
              
            third_octet = message.split()[2]  # Tomamos el tercer octeto

            # Decodificar la extensión
            adsb_ep = third_octet[0]  # Bit 8 (ADSB#EP)
            adsb_val = third_octet[1]  # Bit 7 (ADSB#VAL)
            scn_ep = third_octet[2]  # Bit 6 (SCN#EP) Surveillance Cluster Network Information
            scn_val = third_octet[3]    # Bit 5 (SCN#VAL)
            pai_ep = third_octet[4]    # Bit 4 (PAI#EP) Passive Acquisition Interface
            pai_val = third_octet[5]  # Bit 3 (PAI#VAL)
            FX3 = third_octet[7]  # Bit 2 (FX del tercer octeto)

            # Guardar los resultados del tercer octeto en el diccionario
            ADSB_EP = 'ADSB populated' if adsb_ep == '1' else 'ADSB not populated' # ADSB populated bit
            ADSB_VAL = 'Available' if adsb_val == '1' else 'Not Available' # On-Site ADS-B Information
            SCN_EP = 'SCN populated' if scn_ep == '1' else 'SCN not populated' # SCN Element Populated Bit
            SCN_VAL = 'Available' if scn_val == '1' else 'Not Available' # SCN Information
            PAI_EP = 'PAI populated' if pai_ep == '1' else 'PAI not populated' # PAI Element Populated Bit
            PAI_VAL = 'Available' if pai_val == '1' else 'Not Available' # PAI Information



    return TYP, SIM, RDP, SPI, RAB, TST, ERR, XPP, ME, MI, FOE_FRI, ADSB_EP, ADSB_VAL, SCN_EP, SCN_VAL, PAI_EP, PAI_VAL



#message = '11100000'
#resultado = decode_020(message)
#print(resultado)
