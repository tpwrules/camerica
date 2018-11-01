EESchema Schematic File Version 4
LIBS:photon_board-cache
EELAYER 26 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title ""
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L Connector_Generic:Conn_02x20_Odd_Even J1
U 1 1 5BD9CB75
P 1750 2050
F 0 "J1" H 1800 3167 50  0000 C CNN
F 1 "TERASIC" H 1800 3076 50  0000 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical" H 1750 2050 50  0001 C CNN
F 3 "https://www.digikey.com/product-detail/en/sullins-connector-solutions/SFH11-PBPC-D20-ST-BK/S9200-ND/1990093" H 1750 2050 50  0001 C CNN
	1    1750 2050
	1    0    0    -1  
$EndComp
NoConn ~ 1550 1150
NoConn ~ 1550 1250
$Comp
L power:+5V #PWR0101
U 1 1 5BD9CC1E
P 1300 1650
F 0 "#PWR0101" H 1300 1500 50  0001 C CNN
F 1 "+5V" H 1315 1823 50  0000 C CNN
F 2 "" H 1300 1650 50  0001 C CNN
F 3 "" H 1300 1650 50  0001 C CNN
	1    1300 1650
	1    0    0    -1  
$EndComp
Wire Wire Line
	1300 1650 1550 1650
$Comp
L power:+3V3 #PWR0102
U 1 1 5BD9CCF3
P 1300 2550
F 0 "#PWR0102" H 1300 2400 50  0001 C CNN
F 1 "+3V3" H 1315 2723 50  0000 C CNN
F 2 "" H 1300 2550 50  0001 C CNN
F 3 "" H 1300 2550 50  0001 C CNN
	1    1300 2550
	1    0    0    -1  
$EndComp
Wire Wire Line
	1300 2550 1550 2550
$Comp
L power:GND #PWR0103
U 1 1 5BD9CD64
P 2300 1650
F 0 "#PWR0103" H 2300 1400 50  0001 C CNN
F 1 "GND" H 2305 1477 50  0000 C CNN
F 2 "" H 2300 1650 50  0001 C CNN
F 3 "" H 2300 1650 50  0001 C CNN
	1    2300 1650
	1    0    0    -1  
$EndComp
Wire Wire Line
	2300 1650 2050 1650
$Comp
L power:GND #PWR0104
U 1 1 5BD9CDEB
P 2300 2550
F 0 "#PWR0104" H 2300 2300 50  0001 C CNN
F 1 "GND" H 2305 2377 50  0000 C CNN
F 2 "" H 2300 2550 50  0001 C CNN
F 3 "" H 2300 2550 50  0001 C CNN
	1    2300 2550
	1    0    0    -1  
$EndComp
Wire Wire Line
	2300 2550 2050 2550
$Comp
L Connector:DB15_Female_HighDensity_MountingHoles J2
U 1 1 5BD9D048
P 5650 2050
F 0 "J2" H 5650 2917 50  0000 C CNN
F 1 "PHOTON" H 5650 2826 50  0000 C CNN
F 2 "Connector_Dsub:DSUB-15-HD_Female_Horizontal_P2.29x1.98mm_EdgePinOffset3.03mm_Housed_MountingHolesOffset4.94mm" H 4700 2450 50  0001 C CNN
F 3 " ~" H 4700 2450 50  0001 C CNN
	1    5650 2050
	1    0    0    -1  
$EndComp
$Comp
L power:GND #PWR0105
U 1 1 5BD9D12F
P 5650 2750
F 0 "#PWR0105" H 5650 2500 50  0001 C CNN
F 1 "GND" H 5655 2577 50  0000 C CNN
F 2 "" H 5650 2750 50  0001 C CNN
F 3 "" H 5650 2750 50  0001 C CNN
	1    5650 2750
	1    0    0    -1  
$EndComp
Text Label 5350 1650 2    50   ~ 0
DATA_SYNC+
Text Label 5350 1850 2    50   ~ 0
DATA1_OUT+
Text Label 5350 2050 2    50   ~ 0
DATA2_OUT+
Text Label 5350 2250 2    50   ~ 0
DATA_CLK+
Text Label 5350 1550 2    50   ~ 0
DATA_SYNC-
Text Label 5350 1750 2    50   ~ 0
DATA1_OUT-
Text Label 5350 1950 2    50   ~ 0
DATA2_OUT-
Text Label 5350 2150 2    50   ~ 0
DATA_CLK-
$Comp
L power:GND #PWR0106
U 1 1 5BD9D377
P 5000 2350
F 0 "#PWR0106" H 5000 2100 50  0001 C CNN
F 1 "GND" H 5005 2177 50  0000 C CNN
F 2 "" H 5000 2350 50  0001 C CNN
F 3 "" H 5000 2350 50  0001 C CNN
	1    5000 2350
	1    0    0    -1  
$EndComp
Wire Wire Line
	5000 2350 5350 2350
NoConn ~ 5350 2450
NoConn ~ 5950 2050
NoConn ~ 5950 2250
NoConn ~ 5950 2450
$Comp
L photon_board:SN65LVDT34D U?
U 1 1 5BDA5F0C
P 3450 1450
F 0 "U?" H 3450 2228 50  0000 C CNN
F 1 "SN65LVDT34D" H 3450 2137 50  0000 C CNN
F 2 "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm" H 3400 800 50  0001 C CNN
F 3 "https://www.digikey.com/product-detail/en/texas-instruments/SN65LVDT34D/296-9751-5-ND/380393" H 2750 600 50  0001 C CNN
	1    3450 1450
	-1   0    0    -1  
$EndComp
$Comp
L photon_board:SN65LVDT34D U?
U 1 1 5BDA6017
P 3450 3000
F 0 "U?" H 3450 3778 50  0000 C CNN
F 1 "SN65LVDT34D" H 3450 3687 50  0000 C CNN
F 2 "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm" H 3400 2350 50  0001 C CNN
F 3 "https://www.digikey.com/product-detail/en/texas-instruments/SN65LVDT34D/296-9751-5-ND/380393" H 2750 2150 50  0001 C CNN
	1    3450 3000
	-1   0    0    -1  
$EndComp
$EndSCHEMATC
