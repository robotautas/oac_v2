from ulab import numpy as np
from pyb import ADC, Pin, Timer
from utime import sleep_us, ticks_us
#import time
import gc

SIMULATOR          = True
TIMER_FREQ         = 13100 if SIMULATOR else 1000000
WAVE_LENGTH        = 1000 if SIMULATOR else 1000
WAVES_COUNT        = 10
WAVES_LENGTH       = WAVE_LENGTH * (WAVES_COUNT + 1)

START    = 300
BOTTOM_A = 520
BOTTOM_B = 630

#if SIMULATOR:
    #START    = round(WAVE_LENGTH / 1000 * START)
    #BOTTOM_A = round(WAVE_LENGTH / 1000 * BOTTOM_A)
    #BOTTOM_B = round(WAVE_LENGTH / 1000 * BOTTOM_B)

adc = ADC(Pin('A0'))
tim = Timer(2, freq=TIMER_FREQ)
buf = bytearray(WAVES_LENGTH)
adc.read_timed(buf, tim)

def test_wave_splitter(arr, wave_len, fall):
    '''
    variantas triukšmingam nuskaitymui
    suranda bangos pražią, grąžina bangos pradžių indeksus vėlesniam nuskaitymo suskirstymui į bangas:
    fall - tarp kiek narių ieškomas didžiausias perkritimas, laikomas bangos pabaiga
    '''
    # surandame tašką, kur didžiausias perkritimas žemyn
    max_diff_idx = np.argmin(arr[:wave_len][fall:]-arr[:wave_len][:-fall]) + fall
    # nuo to taško imame nedidelį submasyvą. Jo minimumas bus pirmos bangos pradžia.
    split_point = np.argmin(arr[max_diff_idx:max_diff_idx + 100]) + max_diff_idx
    # surandama, kiek sveikų bangų masyve
    waves_count = len(arr[split_point:])//wave_len
    # surandamos likusių bangų pradžios
    split_points = [split_point,]
    last_point = split_point
    for i in range(waves_count):
        last_point += wave_len
        split_points.append(last_point)
    # grąžinamos masyve visos sveikų bangų pradžios (paskutinė nepilna)
    return split_points[:-1]

def get_area(arr, start_a, bottom_a, bottom_b):
    '''paprastas variantas, darant prielaidą, kad pikai rasis maždaug ten pat, taip pat
    piko pabaiga bus pikas į viršų
    arr - paduodamas masyvas, vienos bangos ilgio
    start_a - diapazono pradžia piko pradžios paieškai
    bottom_a, bottom_b - diapazonas, kuriame tikimės piko'''
    # surandamas piko apačios indeksas
    peak_negative = np.argmin(arr[bottom_a:bottom_b]) + bottom_a

    # surandamas piko pradžios indeksas
    # kadangi argmax() ieško pirmo maksimalalios vertes indekso, ieškome apsukę diapazoną
    start_idx_reversed = np.argmax(arr[start_a:peak_negative][::-1])
    start_idx = peak_negative - start_idx_reversed - 1
    # jeigu pikas yra spyglys. If bloką galima iškomentuoti, jei nuspyglinimas nedomina.
    #if arr[start_idx - 1] == arr[start_idx + 1]:
        #print("spyglys!")
        # pikas yra spyglio pagrindo aukštyje. Perstumiamas į tą vietą, kur tokia reikšmė pirmą kartą atsiranda atkarpoje.
        #start_idx_reversed = np.argmax(arr[start_a:peak_negative][::-1] == arr[start_idx-1])
        #start_idx = peak_negative - start_idx_reversed - 1
        #print(f'pataisytas: {start_idx}')

    # surandamas piko pabaigos indeksas
    end_idx = np.argmax(arr[peak_negative: peak_negative + 150]) + peak_negative
    # transformuojama piko atkarpa (paruošiama integracijai)
    # y ašis perslenkama taip, kad max vertė atsidurtų ties 0, apverčiama
    peak = (arr[start_idx:end_idx+1]-max(arr[start_idx:end_idx+1]))*-1
    time_axis = np.arange(0, len(peak))
    # panaudojama numpy trapz funkcija ploto suintegravimui
    # atimamas trikampis kur a - piko ilgis, b - skirtumas tarp pradžios ir pabaigos
    a = float(len(peak) - 1)
    # kadangi paruošto piko min = 0, parenkamas tiesiog galas su didesne verte
    b = max([peak[0], peak[-1]]) if peak[0]!=peak[-1] else 0
    area = np.trapz(peak, time_axis) - a*b/2
    # grąžinamas plotas
    # grąžinami piko pradžios, apačios ir pabaigos taškai (spausdinimui notebook'o aplinkoje)
    return area, start_idx, peak_negative, end_idx
counter = 1
while True:
    #start_time = ticks_us()
    adc.read_timed(buf, tim)
    start_time = ticks_us()
    reading = np.array(buf) / 77.56
    split_points = test_wave_splitter(reading, WAVE_LENGTH, 10)
    ten_waves = [reading[i:i+WAVE_LENGTH] for i in split_points][:10]
    avg_wave = np.mean(np.array(ten_waves), axis=0)
    area, start_idx, peak_negative, end_idx = get_area(avg_wave, START, BOTTOM_A, BOTTOM_B)
    print(counter, "AREA: ", area, start_idx, peak_negative, end_idx)
    #print('MEMORY: ', gc.mem_free())
    del reading

    del ten_waves
    #gc.collect()
    del avg_wave
    gc.collect()
    counter += 1
    time_delta = ticks_us() - start_time
    print("time: ", time_delta/1000000)
    #print('MEMORY: ', gc.mem_free())
    #sleep_us(10)

#print(split_points)

#np.set_printoptions(threshold=WAVES_LENGTH)
#print(reading)
#print(avg_wave)
#print("AREA: ", area, start_idx, peak_negative, end_idx)

