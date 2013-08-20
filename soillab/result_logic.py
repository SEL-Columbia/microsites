# encoding=utf-8

from collections import OrderedDict


def soil_results(sample):

    def level_in_range(value, levels):
        for max_value, level in levels.iteritems():
            if not isinstance(max_value, (int, float)):
                return level
            if value < max_value:
                return level
        return levels[-1]

    # initialize results dict with labels
    n = 'name'
    v = 'value'
    b = 'badge'
    lvl = 'level_text'
    lvlt = 'level_text_verbose'
    u = 'unit'

    lvlel = u"Extremely Low"
    lvlvl = u"Very Low"
    lvll = u"Low"
    lvlm = u"Medium"
    lvlmh = u"Medium/High"
    lvlh = u"High"
    lvlvh = u"Very High"
    # lvlg = u"Good"
    lvlo = u"Optimal"
    lvlb = u"No Data"

    bvl = 'important'  # very low
    bvh = 'important'  # very high
    bred = 'important'
    bl = 'warning'  # low
    bh = 'warning'  # high
    bm = 'warning'
    byellow = 'warning'
    bn = 'info'  # neutral
    # bblue = 'info'
    # bg = 'success'  # good
    bgreen = 'success'
    # bb = 'inverse'  # blank
    # bblack = 'inverse'
    bno = None

    udsm = u"deciS/m"
    umgc3 = u"mg/㎤"
    umgkg = u"mg/kg"
    un = None

    # initialize the result dict for ordering.
    results = OrderedDict([
        ('ec', {n: u"Soluble Salts", v: 0, b: bno, lvl: lvlb, u: udsm}),
        ('ph_water', {n: u"Water pH", v: 0, b: bno, lvl: lvlb, u: un}),
        ('ph_cacl', {n: u"Salt pH", v: 0, b: bno, lvl: lvlb, u: un}),
        ('ph_cacl_reco', {n: u"pH Recommendation", v: 0, b: bno, lvl: lvlb, u: un}),
        ('delta_ph', {n: u"Δ pH", v: 0, b: bno, lvl: lvlb, u: un}),
        ('soil_bulk_density', {n: u"Soil Bulk Density", v: 0, b: bno, lvl: lvlb, u: umgc3}),
        ('soil_moisture', {n: u"Soil Moisture at Sampling", v: 0, b: bno, lvl: lvlb, u: un}),
        ('soil_type', {n: u"Lime Recommendation", v: 0, b: bno, lvl: lvlb, u: un}),
        ('soil_nitrate', {n: u"Soil Nitrate-N (NO3—N)", v: 0, b: bno, lvl: lvlb, u: umgkg}),
        ('soil_potassium', {n: u"Soil Potassium (K)", v: 0, b: bno, lvl: lvlb, u: umgkg}),
        ('soil_phosphorus', {n: u"Soil Phosphorus (PO4--P)", v: 0, b: bno, lvl: lvlb, u: umgkg}),
        ('soil_sulfate', {n: u"Soil Sulfate (SO4--S)", v: 0, b: bno, lvl: lvlb, u: umgkg}),
        # ('soil_organic_matter', {n: u"Soil Organic Matter", v: 0, b: bno, lvl: lvlb}),
        ('active_carbon', {n: u"Active Carbon", v: 0, b: bno, lvl: lvlb}),
    ])

    #
    # EC GROUP
    #
    soil_units = {
        'microseimens_per_cm': 0.001,
        'parts_per_million': 1.0 / 500,
        'milliseimens_per_cm': 1.0,
        'decisiemens_per_meter': 1.0,
        'mmhos_per_cm': 1.0,
    }

    ec_levels = OrderedDict([
        (0.1, {b: bl, lvl: lvll, lvlt: u"Low fertility, leached nutrients."}),
        (0.3, {b: bm, lvl: lvlm, lvlt: u"Medium fertility, especially in acid soils."}),
        (0.6, {b: bn, lvl: lvlm, lvlt: u"Slightly saline. Limiting for salt-sensitive crops."}),
        (1.2, {b: bh, lvl: lvlh, lvlt: u"Very saline. Limiting for salt-sensitive crops. Some intolerance for salt-enduring crops."}),
        (2.4, {b: bh, lvl: lvlh, lvlt: u"Severe salinity. Strong limitations for both salt-sensitive and tolerant crops."}),
        (4.0, {b: bvh, lvl: lvlvh, lvlt: u"Very severe salinity. Few crops survive."}),
        ('_', {b: bvh, lvl: lvlvh, lvlt: u"Very few crops can grow."}),
        ])

    try:
        sample_ec = float(sample.get('ec_sample_ec', None))
        blank_ec = float(sample.get('ec_blank_ec', None))
        soil_ec = sample_ec - blank_ec
    except:
        soil_ec = None

    try:
        results['ec'][v] = soil_ec * float(soil_units.get(sample.get('ec_units', None), None))
    except:
        results['ec'][v] = None

    # update badge levels
    if not results['ec'][v] is None:
        results['ec'].update(level_in_range(results['ec'][v], ec_levels))

    #
    # pH H2O
    #
    try:
        results['ph_water'][v] = float(sample.get('ph_water_sample_ph_water', None))
    except:
        results['ph_water'][v] = None

    #
    # pH CaCl
    #
    ph_cacl_levels = OrderedDict([
        (4.0, {b: bred, lvl: lvlvl, lvlt: u"pH is limiting: soil exhibits severe aluminum toxicity"}),
        (5.0, {b: bred, lvl: lvll, lvlt: u"pH is limiting: soil exhibits aluminum and manganese toxicity."}),
        (5.5, {b: byellow, lvl: lvlm, lvlt: u"pH is somewhat limiting."}),
        (6.5, {b: bgreen, lvl: lvlo, lvlt: u"Optimal pH for good plant productivity."}),
        (7.5, {b: bgreen, lvl: lvlh, lvlt: u"pH is not limiting. However, may be Fe, Mn, Zn deficiencies in sandy soils."}),
        (8.5, {b: bred, lvl: lvlh, lvlt: u"pH is somewhat limiting (calcareous soil). Will likely observe Fe, Mn, Zn, deficiencies."}),
        ('_', {b: bred, lvl: lvlvh, lvlt: u"Severe pH limitations with sodium problems (sodic)"}),
        ])

    try:
        results['ph_cacl'][v] = float(sample.get('ph_cacl2_sample_ph_cacl2', None))
    except:
        results['ph_cacl'][v] = None

     # update badge levels
    if not results['ph_cacl'][v] is None:
        results['ph_cacl'].update(level_in_range(results['ph_cacl'][v], ph_cacl_levels))

    #
    # pH recomendation
    #
    rec_nutrients = {
        'n': {
            1: u"Urine, manure, DAP, Potassium nitrate, NPK, limit use of urea, avoid ammonium sulfate",
            2: u"Urine, manure, DAP, Potassium nitrate, NPK, limit use of urea, avoid ammonium sulfate",
            3: u"Urine, manure, urea, DAP, Potassium nitrate, NPK, limit use of Ammonium Sulfate",
            4: u"Urine, manure, urea, DAP, Potassium nitrate, NPK, Ammonium Sulfate",
            5: u"Urine, manure, urea, Ammonium Sulfate, DAP, Potassium nitrate, NPK",
            6: u"Urine, manure, Ammonium Sulfate, DAP, Potassium nitrate, NPK, limit use of Urea",
            7: u"Urine, manure, Ammonium Sulfate, DAP, Potassium nitrate, NPK, limit use of Urea",
        },
        'p': {
            1: u"DAP, NPK, Triple Super Phosphate, Phosphate rock, urine, ash",
            2: u"DAP, NPK, Triple Super Phosphate, Phosphate rock, urine, ash",
            3: u"DAP, NPK, Triple Super Phosphate, Phosphate rock, urine, ash",
            4: u"DAP, NPK, Triple Super Phosphate, Phosphate rock, urine, ash",
            5: u"DAP, NPK, Triple Super Phosphate, Phosphate rock, urine, ash",
            6: u"DAP, NPK, Triple Super Phosphate, Phosphate rock, Urine, limit ash",
            7: u"DAP, NPK, Triple Super Phosphate, Phosphate rock, urine, avoid ash",
        },
        'k': {
            1: u"Urine, Ash, NPK, Potash, Potassium nitrate",
            2: u"Urine, Ash, NPK, Potash, Potassium nitrate",
            3: u"Urine, Ash, NPK, Potash, Potassium nitrate",
            4: u"Urine, Ash, NPK, Potash, Potassium nitrate",
            5: u"Urine, Ash, NPK, Potash, Potassium nitrate",
            6: u"Urine, NPK, Potash, Potassium nitrate, Limit use of ash",
            7: u"Urine, NPK, Potash, Potassium nitrate, avoid ash",
        },
        's': {
            1: u"Gypsum, Potassium sulphate, Epson Magnesium sulphate, Urine, ash, avoid Ammonium Sulfate",
            2: u"Gypsum, Potassium sulphate, Epson Magnesium sulphate, Urine, ash, avoid Ammonium Sulfate",
            3: u"Gypsum, Potassium sulphate, Epson Magnesium sulphate, Urine, ash, avoid Ammonium Sulfate",
            4: u"Gypsum, Potassium sulphate, Epson Magnesium sulphate, Urine, ash, limit Ammonium Sulfate",
            5: u"Gypsum, Ammonium Sulfate, Potassium sulphate, Epson Magnesium sulphate, Urine, ash",
            6: u"Gypsum,  Ammonium Sulfate, Potassium sulphate, Epson Magnesium sulphate, Urine, limit use of ash",
            7: u"Gypsum,  Ammonium Sulfate, Potassium sulphate, Epson Magnesium sulphate, Urine, avoid ash",
        }
    }

    def txtreco(num, text):
        gt = lambda l: rec_nutrients.get(l, {}).get(num)
        return u"{text} N ({n}), P ({p}), K ({k}), S ({s})".format(text=text,
                                                                   n=gt('n'),
                                                                   p=gt('p'),
                                                                   k=gt('k'),
                                                                   s=gt('s'))

    if results['ph_cacl'][lvl] in (lvlvl, lvll):
        results['ph_cacl_reco'][v] = txtreco(1, u"Apply ash or lime, apply manure, green manure.")
    elif results['ph_cacl'][lvl] == lvlm:
        results['ph_cacl_reco'][v] = txtreco(3, u"Avoid acidifying fertilizer such as ammonium "
                                                u"sulfate. Limit use of  urea. May be some "
                                                u"value in applying ash or lime.")
    elif results['ph_cacl'][lvl] == lvlo:
        results['ph_cacl_reco'][v] = txtreco(4, u"Monitor pH for changes")
    elif results['ph_cacl'][lvl] == lvlh and results['ph_cacl'][v] < 7.5:
        results['ph_cacl_reco'][v] = txtreco(5, u"Apply manure and use green manure")
    elif results['ph_cacl'][lvl] == lvlh and results['ph_cacl'][v] >= 7.5:
        results['ph_cacl_reco'][v] = txtreco(6, u"Use caution when applying urea. "
                                                u"Apply sulfur (ammonium sulfate "
                                                u"or elemental) and manure.")
    elif results['ph_cacl'][lvl] == lvlvh:
        results['ph_cacl_reco'][v] = txtreco(7, u"Apply gypsum. Avoid urea and ash.")
    else:
        results['ph_cacl_reco'][v] = None



    #
    # Δ pH
    #
    try:
        sample_ph_water = float(sample.get('ph_water_sample_ph_water', None))
        sample_ph_cacl2 = float(sample.get('ph_cacl2_sample_ph_cacl2', None))
        results['delta_ph'][v] = sample_ph_water - sample_ph_cacl2
    except:
        results['delta_ph'][v] = None

    #
    # soil bulk density
    #
    soil_densities = {
        'coarse': 1.6,
        'moderately_coarse': 1.4,
        'medium': 1.2,
        'fine': 1.0
    }
    try:
        sample_soil_texture = sample.get('sample_id_sample_soil_texture', None)
        results['soil_bulk_density'][v] = float(soil_densities.get(sample_soil_texture, None))
    except:
        results['soil_bulk_density'][v] = None

    #
    # soil moisture at sampling
    #
    try:
        automated_soil_moisture = float(sample.get('sample_id_sample_automated_soil_moisture', None))
        if automated_soil_moisture > 1.0:
            automated_soil_moisture = automated_soil_moisture / 100.0
        soil_bulk_density = float(results['soil_bulk_density'][v])
        results['soil_moisture'][v] = automated_soil_moisture / soil_bulk_density
    except:
        results['soil_moisture'][v] = None

    # select a soil moisture if not provided by measurement
    soil_moisture = None
    if results['soil_moisture'][v] is None:
        texture = sample.get('sample_id_sample_soil_texture', None)
        moisture = sample.get('sample_id_sample_soil_moisture', None)
        if texture and moisture:
            if texture == 'coarse' and moisture == 'field_capacity':
                soil_moisture = 0.115
            elif texture == 'coarse' and moisture == 'half_field_capacity':
                soil_moisture = 0.078
            elif texture == 'coarse' and moisture == 'wilting_point':
                soil_moisture = 0.004
            elif texture == 'coarse' and moisture == 'air_dry':
                soil_moisture = 0.002
            elif texture == 'moderately_coarse' and moisture == 'field_capacity':
                soil_moisture = 0.185
            elif texture == 'moderately_coarse' and moisture == 'half_field_capacity':
                soil_moisture = 0.123
            elif texture == 'moderately_coarse' and moisture == 'wilting_point':
                soil_moisture = 0.06
            elif texture == 'moderately_coarse' and moisture == 'air_dry':
                soil_moisture = 0.03
            elif texture == 'medium' and moisture == 'field_capacity':
                soil_moisture = 0.250
            elif texture == 'medium' and moisture == 'half_field_capacity':
                soil_moisture = 0.175
            elif texture == 'medium' and moisture == 'wilting_point':
                soil_moisture = 0.10
            elif texture == 'medium' and moisture == 'air_dry':
                soil_moisture = 0.05
            elif texture == 'fine' and moisture == 'field_capacity':
                soil_moisture = 0.317
            elif texture == 'fine' and moisture == 'half_field_capacity':
                soil_moisture = 0.233
            elif texture == 'fine' and moisture == 'wilting_point':
                soil_moisture = 0.15
            elif texture == 'fine' and moisture == 'air_dry':
                soil_moisture = 0.075
        if soil_moisture is not None:
            results['soil_moisture'][v] = soil_moisture

    try:
        percent_moisture_by_weight = float(results['soil_moisture'][v])
    except:
        percent_moisture_by_weight = None

    #
    # soil type & Lime recommendation
    #
    try:
        results['soil_type'][v] = sample.get('soil_type_sample_soil_type', None)
    except:
        results['soil_type'][v] = None

    def get_lime_reco(soil_type, water_ph):
        if not soil_type or not water_ph:
            return None

        if soil_type == 'black_cracking_clay' and water_ph > 3.8 and water_ph < 4.3: return u"18 MT CaCO3 eq. (Lime or Ash)/ha"
        if soil_type == 'black_cracking_clay' and water_ph > 4.4 and water_ph < 4.8: return u"9 MT CaCO3 eq. (Lime or Ash)/ha"
        if soil_type == 'black_cracking_clay' and water_ph > 4.9 and water_ph < 5.3: return u"4.5 MT CaCO3 eq. (Lime or Ash)/ha"
        if soil_type == 'black_cracking_clay' and water_ph > 5.4 and water_ph < 7.9: return u"No action required."
        if soil_type == 'black_cracking_clay' and water_ph > 8.0 and water_ph < 8.0: return u"6 MT S°/ha"
        if soil_type == 'black_cracking_clay' and water_ph > 9.0 and water_ph < 9.5: return u"12 MT S°/ha"

        if soil_type == 'red_clay' and water_ph > 3.8 and water_ph < 4.3: return u"5 MT CaCO3 eq. (Lime or Ash)/ha"
        if soil_type == 'red_clay' and water_ph > 4.4 and water_ph < 4.8: return u"2.5 MT CaCO3 eq. (Lime or Ash)/ha"
        if soil_type == 'red_clay' and water_ph > 4.9 and water_ph < 5.3: return u"1.2 MT CaCO3 eq. (Lime or Ash)/ha"
        if soil_type == 'red_clay' and water_ph > 5.4 and water_ph < 7.9: return u"No action required."
        if soil_type == 'red_clay' and water_ph > 8.0 and water_ph < 8.0: return u"1.2 MT S°/ha"
        if soil_type == 'red_clay' and water_ph > 9.0 and water_ph < 9.5: return u"2.4 MT S°/ha"

        if soil_type == 'brown_loamy' and water_ph > 3.8 and water_ph < 4.3: return u"6 MT CaCO3 eq. (Lime or Ash)/ha"
        if soil_type == 'brown_loamy' and water_ph > 4.4 and water_ph < 4.8: return u"3 MT CaCO3 eq. (Lime or Ash)/ha"
        if soil_type == 'brown_loamy' and water_ph > 4.9 and water_ph < 5.3: return u"1.5 MT CaCO3 eq. (Lime or Ash)/ha"
        if soil_type == 'brown_loamy' and water_ph > 5.4 and water_ph < 7.9: return u"No action required."
        if soil_type == 'brown_loamy' and water_ph > 8.0 and water_ph < 8.0: return u"2 MT S°/ha"
        if soil_type == 'brown_loamy' and water_ph > 9.0 and water_ph < 9.5: return u"4 MT S°/ha"

        if soil_type == 'sandy' and water_ph > 3.8 and water_ph < 4.3: return u"3 MT CaCO3 eq. (Lime or Ash)/ha"
        if soil_type == 'sandy' and water_ph > 4.4 and water_ph < 4.8: return u"1.5 MT CaCO3 eq. (Lime or Ash)/ha"
        if soil_type == 'sandy' and water_ph > 4.9 and water_ph < 5.3: return u"0.7 MT CaCO3 eq. (Lime or Ash)/ha"
        if soil_type == 'sandy' and water_ph > 5.4 and water_ph < 7.9: return u"No action required."
        if soil_type == 'sandy' and water_ph > 8.0 and water_ph < 8.0: return u"1 MT S°/ha"
        if soil_type == 'sandy' and water_ph > 9.0 and water_ph < 9.5: return u"2 MT S°/ha"

    recommendation = get_lime_reco(results['soil_type'][v], results['ph_water'][v])
    if recommendation:
        results['soil_type'][lvlt] = u"Lime Recommendation: %s" % recommendation

    #
    # soil nitrate
    #
    nitrate_fertility_levels = OrderedDict([
        (21, {b: bvl, lvl: lvlvl, lvlt: u"Yes, Full N recommended."}),
        (42, {b: bl, lvl: lvll, lvlt: u"Yes, ¾ N recommended."}),
        (65, {b: bm, lvl: lvlm, lvlt: u"Yes, ½ N recommended."}),
        (90, {b: bh, lvl: lvlmh, lvlt: u"Yes, ¼ N recommended."}),
        (120, {b: bh, lvl: lvlh, lvlt: u"No N more recommended."}),
        ('_', {b: bvh, lvl: lvlvh, lvlt: u"No N recommended."}),
        ])

    try:
        sample_nitrate = float(sample.get('nitrate_sample_nitrate', None))
        blank_nitrate = float(sample.get('nitrate_blank_nitrate', None))
        results['soil_nitrate'][v] = (
                                      (sample_nitrate - blank_nitrate)
                                      * (20.0
                                         / (1 - (percent_moisture_by_weight * 10.0))))
        # results['soil_nitrate'][v] = (
        #                               (sample_nitrate - blank_nitrate)
        #                               * (20.0
        #                                  / ((1.0 - percent_moisture_by_weight) * 10.0))
        #                               ) * (1 / 4.42)

    except:
        results['soil_nitrate'][v] = None

     # update badge levels
    if results['soil_nitrate'][v] is not None:
        results['soil_nitrate'].update(level_in_range(results['soil_nitrate'][v], nitrate_fertility_levels))

    #
    # soil potassium
    #
    potassium_fertility_levels = OrderedDict([
        (30, {b: bvl, lvl: lvlvl, lvlt: u"K fertilizer needed: Very Likely."}),
        (60, {b: bl, lvl: lvll, lvlt: u"K fertilizer needed: Likely."}),
        (90, {b: bm, lvl: lvlm, lvlt: u"K fertilizer needed: 50/50."}),
        (120, {b: bh, lvl: lvlh, lvlt: u"K fertilizer needed: Unlikely."}),
        ('_', {b: bvh, lvl: lvlvh, lvlt: u"No K fertilizer needed."}),
        ])

    try:
        sample_potassium = float(sample.get('potassium_sample_potassium', None))
        blank_potassium = float(sample.get('potassium_blank_potassium', None))
        results['soil_potassium'][v] = (
                                        (sample_potassium - blank_potassium)
                                        * (20.0
                                           / (1.0 - (percent_moisture_by_weight * 10.0))))

        # results['soil_potassium'][v] = (
        #                                 (sample_potassium - blank_potassium)
        #                                 * (30.0
        #                                    / ((1.0 - percent_moisture_by_weight) * 15.0))
        #                                 )
    except:
        results['soil_potassium'][v] = None

     # update badge levels
    if results['soil_potassium'][v] is not None:
        results['soil_potassium'].update(level_in_range(results['soil_potassium'][v], potassium_fertility_levels))

    #
    # soil phosphorus
    #
    phosphorus_fertility_levels = OrderedDict([
        (0.05, {b: bvl, lvl: lvlel, lvlt: u"Increasing P is top priority."}),
        (0.1, {b: bvl, lvl: lvlvl, lvlt: u"P fertilizer needed: Very Likely."}),
        (0.3, {b: bl, lvl: lvll, lvlt: u"P fertilizer needed: Likely."}),
        (0.5, {b: bm, lvl: lvlm, lvlt: u"P fertilizer needed: 50/50 chance of response."}),
        ('_', {b: bh, lvl: lvlh, lvlt: u"No P fertilizer needed."}),
        ])

    try:
        sample_phosphorus_ppb_meter = float(sample.get('phosphorus_ppb_meter_sample_phosphorus_ppb_meter', None))
        blank_phosphorus_ppb_meter = float(sample.get('phosphorus_ppb_meter_blank_phosphorus_ppb_meter', None))
        soil_phosphorus_ppb = ((sample_phosphorus_ppb_meter - blank_phosphorus_ppb_meter)
                              * (10.0 / 2) * (20.0 / (1.0 - (percent_moisture_by_weight * 10.0))))

        # soil_phosphorus_ppb = (
        #                         (
        #                          (sample_phosphorus_ppb_meter - blank_phosphorus_ppb_meter)
        #                          * (10.0 / 2.0)
        #                          * (30.0 /
        #                             ((1.0 - percent_moisture_by_weight) * 15.0))
        #                         ) / 1000
        #                       )
    except:
        soil_phosphorus_ppb = None

    try:
        sample_phosphorus_ppm_meter = float(sample.get('phosphorus_ppm_meter_sample_phosphorus_ppm_meter', None))
        blank_phosphorus_ppm_meter = float(sample.get('phosphorus_ppm_meter_blank_phosphorus_ppm_meter', None))
        soil_phosphorus_ppm = ((sample_phosphorus_ppm_meter - blank_phosphorus_ppm_meter)
                               * (10.0 / 2) * (20.0 / (1.0 - (percent_moisture_by_weight * 10.0))))

        # (${sample_phosphorus_ppm_meter_x}-${phosphorus_ppm_zero})*(10/2)*(20/(1-(${percent_moisture_by_weight_x}*10)))*(30.97/94.97)
        # soil_phosphorus_ppm = (
        #                        (
        #                         (sample_phosphorus_ppm_meter - blank_phosphorus_ppm_meter)
        #                         * (10.0 / 2.0)
        #                         * (30.0 / ((1.0 - percent_moisture_by_weight) * 15.0))
        #                         * (30.97 / 94.97)
        #                        )
        #                       )
    except:
        soil_phosphorus_ppm = None

    # PPB measure is preffered over PPM but might not be available.
    if soil_phosphorus_ppb is None:
        results['soil_phosphorus'][v] = soil_phosphorus_ppm
    else:
        results['soil_phosphorus'][v] = soil_phosphorus_ppb

     # update badge levels
    if results['soil_phosphorus'][v] is not None:
        results['soil_phosphorus'].update(level_in_range(results['soil_phosphorus'][v], phosphorus_fertility_levels))

    #
    # soil sulfate
    #
    sulfate_fertility_levels = OrderedDict([
        (10, {b: bvl, lvl: lvlvl, lvlt: u"S fertilizer needed: Very Likely."}),
        (15, {b: bl, lvl: lvll, lvlt: u"S fertilizer needed: Likely."}),
        (20, {b: bm, lvl: lvlm, lvlt: u"S fertilizer needed: 50/50 chance of response."}),
        ('_', {b: bh, lvl: lvlh, lvlt: u"No S fertilizer needed."}),
        ])

    try:
        sulfur_analysis_vial_ppb = float(sample.get('sulfur_ppb_meter_low_spike_sulfur_analysis_vial_ppb', None))
        slope_low_spike_ppb = 8.0 / sulfur_analysis_vial_ppb
    except:
        slope_low_spike_ppb = None

    try:
        sulfur_analysis_vial_ppm = float(sample.get('sulfur_ppm_meter_high_spike_sulfur_analysis_vial_ppm', None))
        slope_high_spike_ppm = 16.0 / sulfur_analysis_vial_ppm
    except:
        slope_high_spike_ppm = None

    try:
        sample_sulfur_ppb_meter = float(sample.get('sulfur_ppb_meter_sample_sulfur_ppb_meter', None))
        sulfur_analysis_vial_extract = float(sample.get('s_spike_and_dilution_sample_sulfur_analysis_vial_extract', None))
        sulfur_analysis_vial_water = float(sample.get('s_spike_and_dilution_sample_sulfur_analysis_vial_water', None))

        soil_sulfur_ppb = (
                          sample_sulfur_ppb_meter
                          * slope_low_spike_ppb
                          * (sulfur_analysis_vial_extract + sulfur_analysis_vial_water)
                          / sulfur_analysis_vial_extract
                          * (30.0 / ((1.0 - percent_moisture_by_weight) * 15.0))
                          )

    except:
        soil_sulfur_ppb = None

    try:
        sample_sulfur_ppm_meter = float(sample.get('sulfur_ppm_meter_sample_sulfur_ppm_meter', None))
        sulfur_analysis_vial_extract = float(sample.get('s_spike_and_dilution_sample_sulfur_analysis_vial_extract', None))
        sulfur_analysis_vial_water = float(sample.get('s_spike_and_dilution_sample_sulfur_analysis_vial_water', None))

        soil_sulfur_ppm = (
                           sample_sulfur_ppm_meter
                           * slope_high_spike_ppm
                           * (sulfur_analysis_vial_extract + sulfur_analysis_vial_water)
                           / sulfur_analysis_vial_extract
                           * (30.0 / ((1.0 - percent_moisture_by_weight) * 15.0))
                          )
    except:
        soil_sulfur_ppm = None

    # PPB measure is preffered over PPM but might not be available.
    if soil_sulfur_ppb is None:
        results['soil_sulfate'][v] = soil_sulfur_ppm
    else:
        results['soil_sulfate'][v] = soil_sulfur_ppb

     # update badge levels
    if results['soil_sulfate'][v] is not None:
        results['soil_sulfate'].update(level_in_range(results['soil_sulfate'][v], sulfate_fertility_levels))

    #
    # soil organic matter
    #
    # no input

    #
    # active carbon
    #
    try:
        sample_active_carbon_ppm_meter = float(sample.get('active_carbon_ppm_meter_sample_sample_active_carbon_ppm_meter', None))
        results['active_carbon'][v] =  ((0.02 - ( 2 * (0.0055 * (sample_active_carbon_ppm_meter) -0.0002)))
                                        *72000)
    except:
        raise
        results['active_carbon'][v] =  None

    return results
