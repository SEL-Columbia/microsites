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
    lvlg = u"Good"
    lvlo = u"Optimal"
    lvlb = u"No Data"

    bvl = 'important' # very low
    bvh = 'important' # very high
    bl = 'warning' # low
    bh = 'warning' # high
    bh = 'warning' # high
    bn = 'info' # neutral
    bg = 'success' # good
    bb = 'inverse' # blank
    bno = None

    udsm = u"deciS/m"
    umgc3 = u"mg/㎤"
    umgkg = u"mg/kg"
    un = None

    # initialize the result dict for ordering.
    results = OrderedDict([
        ('ec', {n: u"EC", v: 0, b: bno, lvl: lvlb, u: udsm}),
        ('ph_water', {n: u"pH Water", v: 0, b: bno, lvl: lvlb, u: un}),
        ('ph_cacl', {n: u"pH Salt", v: 0, b: bno, lvl: lvlb, u: un}),
        ('delta_ph', {n: u"Δ pH", v: 0, b: bno, lvl: lvlb, u: un}),
        ('soil_bulk_density', {n: u"Soil Bulk Density", v: 0, b: bno, lvl: lvlb, u: umgc3}),
        ('soil_moisture', {n: u"Soil Moisture at Sampling", v: 0, b: bno, lvl: lvlb, u: un}),
        ('soil_nitrate', {n: u"Soil Nitrate", v: 0, b: bno, lvl: lvlb, u: umgkg}),
        ('soil_potassium', {n: u"Soil Potassium", v: 0, b: bno, lvl: lvlb, u: umgkg}),
        ('soil_phosphorus', {n: u"Soil Phosphorus", v: 0, b: bno, lvl: lvlb, u: umgkg}),
        ('soil_sulfate', {n: u"Soil Sulfate", v: 0, b: bno, lvl: lvlb, u: umgkg}),
        # ('soil_organic_matter', {n: u"Soil Organic Matter", v: 0, b: bno, lvl: lvlb}),
    ])

    #
    # EC GROUP
    #
    soil_units = {
        'microseimens_per_cm': 1000.0,
        'parts_per_million': 1.0/500,
        'milliseimens_per_cm': 0.001,
        'decisiemens_per_meter': 1.0,
        'mmhos_per_cm': 1.0,
    }

    ec_levels = OrderedDict([
        (0.1, {b: bl, lvl: lvll, lvlt: u"Low fertility, leached nutrients."}),
        (0.3, {b: bn, lvl: lvlm, lvlt: u"Medium fertility, especially in acid soils."}),
        (0.6, {b: bn, lvl: lvlm, lvlt: u"Slightly saline. Limiting for salt-sensitive crops."}),
        (1.2, {b: bh, lvl: lvlh, lvlt: u"Very saline. Limiting for salt-sensitive crops. Some intolerance for salt-enduring crops."}),
        (2.4, {b: bh, lvl: lvlh, lvlt: u"Severe salinity. Strong limitations for both salt-sensitive and tolerant crops."}),
        (4.0, {b: bvh, lvl: lvlvh, lvlt: u"Very severe salinity. Few crops survive."}),
        ('_', {b: bvh, lvl: lvlvh, lvlt: u"Very few crops can grow."}),
        ])

    try:
        soil_ec = float(sample.get('ec_sample_ec', None)) - float(sample.get('ec_blank_ec', None))
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
        (4.0, {b: bl, lvl: lvll, lvlt: u"pH is limiting: soil exhibits severe aluminum toxicity"}),
        (5.0, {b: bl, lvl: lvll, lvlt: u"pH is limiting: soil exhibits aluminum and manganese toxicity."}),
        (5.5, {b: bn, lvl: lvlm, lvlt: u"pH is somewhat limiting."}),
        (6.5, {b: bg, lvl: lvlo, lvlt: u"Optimal pH for good plant productivity."}),
        (7.5, {b: bh, lvl: lvlh, lvlt: u"pH is not limiting. However, may be Fe, Mn, Zn deficiencies in sandy soils."}),
        (8.5, {b: bh, lvl: lvlh, lvlt: u"pH is somewhat limiting (calcareous soil). Will likely observe Fe, Mn, Zn, deficiencies."}),
        ('_', {b: bvh, lvl: lvlvh, lvlt: u"Severe pH limitations with sodium problems (sodic)"}),
        ])

    try:
        results['ph_cacl'][v] = float(sample.get('ph_cacl2_sample_ph_cacl2', None))
    except:
        results['ph_cacl'][v] = None

     # update badge levels
    if not results['ph_cacl'][v] is None:
        results['ph_cacl'].update(level_in_range(results['ph_cacl'][v], ph_cacl_levels))

    #
    # Δ pH
    #
    try:
        results['delta_ph'][v] = (float(sample.get('ph_water_sample_ph_water')) 
                                  - float(sample.get('ph_cacl2_sample_ph_cacl2')))
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
        results['soil_bulk_density'][v] = float(soil_densities.get(sample.get('sample_id_sample_soil_texture', None), None))
    except:
        results['soil_bulk_density'][v] = None

    #
    # soil moisture at sampling
    #
    try:
        results['soil_moisture'][v] = (float(sample.get('sample_id_sample_automated_soil_moisture', None)) 
                                       / float(results['soil_bulk_density'][v]))
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
    # soil nitrate
    #
    nitrate_fertility_levels = OrderedDict([
        (21, {b: bvl, lvl: lvlvl, lvlt: u"Yes-Full N recommended."}),
        (42, {b: bl, lvl: lvll, lvlt: u"Yes-3/4 N recommended."}),
        (65, {b: bn, lvl: lvlm, lvlt: u"Yes-1/2 N recommended."}),
        (90, {b: bh, lvl: lvlmh, lvlt: u"Yes, 1/4 N recommended."}),
        (120, {b: bh, lvl: lvlh, lvlt: u"No N more recommended."}),
        ('_', {b: bvh, lvl: lvlvh, lvlt: u"No N recommended."}),
        ])

    try:
        results['soil_nitrate'][v] = (
            (float(sample.get('nitrate_sample_nitrate')) 
             - float(sample.get('nitrate_blank_nitrate'))) 
            * (30.0 / ((1.0 - float(percent_moisture_by_weight)) * 15.0)) )
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
        (90, {b: bn, lvl: lvlm, lvlt: u"K fertilizer needed: 50/50."}),
        (120, {b: bh, lvl: lvlh, lvlt: u"K fertilizer needed: Unlikely."}),
        ('_', {b: bvh, lvl: lvlvh, lvlt: u"No K fertilizer needed."}),
        ])

    try:
        results['soil_potassium'][v] = (
            (float(sample.get('potassium_sample_potassium')) 
             - float(sample.get('potassium_blank_potassium'))) 
            * (30.0 / ((1.0 - float(percent_moisture_by_weight)) * 15.0)) )
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
        (0.5, {b: bn, lvl: lvlm, lvlt: u"P fertilizer needed: 50/50 chance of response."}),
        ('_', {b: bh, lvl: lvlh, lvlt: u"No P fertilizer needed."}),
        ])

    try:
        soil_phosphorus_ppb = ((float(sample.get('phosphorus_ppb_meter_blank_phosphorus_ppb_meter', None)) 
                                - float(sample.get('phosphorus_ppb_meter_blank_phosphorus_ppb_meter', None)))
                               * (10.0 / 2.0) 
                               * ( 30.0 / 
                                  ((1.0 - float(percent_moisture_by_weight)) * 15.0)) ) * 1000
    except:
        soil_phosphorus_ppb = None

    try:
        soil_phosphorus_ppm = ((float(sample.get('phosphorus_ppm_meter_sample_phosphorus_ppm_meter', None))
                                - float(sample.get('phosphorus_ppm_meter_blank_phosphorus_ppm_meter')))
                               * (10.0 / 2.0) 
                               * (30.0 / ((1.0 - percent_moisture_by_weight) * 15.0))
                               * (30.97 / 94.97))
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
        (20, {b: bn, lvl: lvlm, lvlt: u"S fertilizer needed: 50/50 chance of response."}),
        ('_', {b: bh, lvl: lvlh, lvlt: u"No S fertilizer needed."}),
        ])

    try:
        slope_low_spike_ppb = 8.0 / float(sample.get('sulfur_ppb_meter_low_spike_sulfur_analysis_vial_ppb', None))
    except:
        slope_low_spike_ppb = None

    try:
        slope_high_spike_ppm = 16.0 / float(sample.get('sulfur_ppm_meter_high_spike_sulfur_analysis_vial_ppm', None))
    except:
        slope_high_spike_ppm = None

    try:
        soil_sulfur_ppb = (((float(sample.get('sulfur_ppb_meter_sample_sulfur_ppb_meter', None)) * float(slope_low_spike_ppb))
                            / float(sample.get('s_spike_and_dilution_sample_sulfur_analysis_vial_extract', None)))
                           * (30.0 / ((1.0 - percent_moisture_by_weight) * 15.0)))
    except:
        soil_sulfur_ppb = None

    try:
        soil_sulfur_ppm = (
                            ((float(sample.get('sulfur_ppm_meter_sample_sulfur_ppm_meter', None)) * float(slope_high_spike_ppm))
                              / float(sample.get('s_spike_and_dilution_sample_sulfur_analysis_vial_extract', None)))
                             * (30.0 / ((1.0 - percent_moisture_by_weight) * 15.0)))
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

    return results