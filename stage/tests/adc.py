"""
Test file for the Raspi ADC module
"""

from ADCPi import ADCPi

# noinspection PyArgumentEqualDefault,PyArgumentEqualDefault,PyArgumentEqualDefault
adc = ADCPi(0x68, 0x69, 18)
adc.set_pga(1)  # Set gain
adc.set_bit_rate(12)  # Adjust timing (lower is faster)
adc.set_conversion_mode(1)  # Set continuous conversion

while True:
    output = list()
    values = [
        adc.read_voltage(1),
        adc.read_voltage(2),
        adc.read_voltage(3),
        adc.read_voltage(4),
        adc.read_voltage(5),
        adc.read_voltage(6),
        adc.read_voltage(7),
        adc.read_voltage(8),
    ]
    for value in values:
        if value == 0.0:  # 0.002471:  # Clamp noise
            value = 0.0
        output.append(value)
    print(output)
