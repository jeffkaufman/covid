import csv
from collections import defaultdict


# rm covid-case* covid-death*; python3 process.py && for x in caseshape deathabs caseabs ; do rm covid-$x-vax-big.png ; montage -tile 5x -geometry 220x covid-$x-vax-* covid-$x-vax-big.png && open covid-$x-vax-big.png ; done

def parse_sheet(fname):
    # state -> yyyy-mm-dd -> total
    states = defaultdict(lambda: defaultdict(int))

    with open(fname) as inf:
        keys = {}
        revkeys = {}
        for i, line in enumerate(csv.reader(inf)):
            if i == 0:
                for j, key in enumerate(line):
                    keys[key] = j
                    revkeys[j] = key
                continue
            state = line[keys["Province_State"]]
            prev = 0
            for j in range(12, len(line)):
                date = revkeys[j]
                m,d,y = date.split("/")
                yyyy_mm_dd = "%s-%s-%s" % (
                    "20" + y, m.zfill(2), d.zfill(2))

                val = int(line[j])

                curval = val - prev
                states[state][yyyy_mm_dd] += curval
                prev = val

    smoothed_states = {}
    for state in states:
        smoothed_states[state] = {}
        
        last_7 = []
        prev_val = 0
        prev_smoothed = 0
        for yyyy_mm_dd in sorted(states[state]):
            val = states[state][yyyy_mm_dd]

            # Look for spikes for deaths being recorded after the fact.  These
            # are important if you care about totals, but misleading if you
            # care about the shape of the pandemic.  Remove them.
            if "deaths" in fname:
                for late_yyyy_mm_dd, late_state, late_amount in [
                        ('2021-07-30', 'Delaware', 130),
                        ('2021-06-11', 'Florida', 245),
                        ('2021-05-27', 'Maryland', 533),
                        ('2021-03-18', 'Kentucky', 423),
                        ('2021-06-01', 'Kentucky', 276),
                        ('2020-09-02', 'Wyoming', 40),
                        ('2021-03-12', 'West Virginia', 163),
                        ('2021-05-27', 'Maryland', 536),
                        ('2021-04-07', 'Oklahoma', 1701),
                        ('2021-03-18', 'Kentucky', 423),
                        ('2020-12-11', 'Iowa', 500),
                        ]:

                    if yyyy_mm_dd == late_yyyy_mm_dd and state == late_state:
                        val -= late_amount                

            # don't show corrections that bring us below zero; those are also
            # from deaths recorded after the fact
            if val < 0:
                val = 0

            last_7.append(val)
            if len(last_7) > 7:
                last_7.pop(0)
            if len(last_7) == 7:
                smoothed = sum(last_7)/7
                smoothed_states[state][yyyy_mm_dd] = smoothed
                prev_smoothed = smoothed

            prev_val = val
                
    return smoothed_states

cases = parse_sheet("COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv")
deaths = parse_sheet("COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv")

#raise Exception("breakpoint")

# Downloaded from https://covid.cdc.gov/covid-data-tracker/#vaccinations_vacc-total-admin-rate-total on 2021-08-07
pop_vaxed = {}
with open("covid19_vaccinations_in_the_united_states.csv") as inf:
    for i, line in enumerate(csv.reader(inf)):
        if i < 3:
            continue
        state = line[0]
        state = {"New York State": "New York"}.get(state, state)

        line[13] # Percent of Total Pop Fully Vaccinated by State of Residence
        line[15] # Percent of 18+ Pop Fully Vaccinated by State of Residence
        line[41] # Percent of 65+ Pop with at least One Dose by State of Residence
        line[43] # Percent of 65+ Pop Fully Vaccinated by State of Residence
        pop_vaxed[state] = line[13]

state_pop = {}
with open("populations.csv") as inf:
    for state, pop in csv.reader(inf):
        state_pop[state] = int(pop)
        
us_state_abbrev = {
        'Alabama': 'AL',
        'Alaska': 'AK',
        'American Samoa': 'AS',
        'Arizona': 'AZ',
        'Arkansas': 'AR',
        'California': 'CA',
        'Colorado': 'CO',
        'Connecticut': 'CT',
        'Delaware': 'DE',
        'District of Columbia': 'DC',
        'Florida': 'FL',
        'Georgia': 'GA',
        'Guam': 'GU',
        'Hawaii': 'HI',
        'Idaho': 'ID',
        'Illinois': 'IL',
        'Indiana': 'IN',
        'Iowa': 'IA',
        'Kansas': 'KS',
        'Kentucky': 'KY',
        'Louisiana': 'LA',
        'Maine': 'ME',
        'Maryland': 'MD',
        'Massachusetts': 'MA',
        'Michigan': 'MI',
        'Minnesota': 'MN',
        'Mississippi': 'MS',
        'Missouri': 'MO',
        'Montana': 'MT',
        'Nebraska': 'NE',
        'Nevada': 'NV',
        'New Hampshire': 'NH',
        'New Jersey': 'NJ',
        'New Mexico': 'NM',
        'New York': 'NY',
        'North Carolina': 'NC',
        'North Dakota': 'ND',
        'Northern Mariana Islands':'MP',
        'Ohio': 'OH',
        'Oklahoma': 'OK',
        'Oregon': 'OR',
        'Pennsylvania': 'PA',
        'Puerto Rico': 'PR',
        'Rhode Island': 'RI',
        'South Carolina': 'SC',
        'South Dakota': 'SD',
        'Tennessee': 'TN',
        'Texas': 'TX',
        'Utah': 'UT',
        'Vermont': 'VT',
        'Virgin Islands': 'VI',
        'Virginia': 'VA',
        'Washington': 'WA',
        'West Virginia': 'WV',
        'Wisconsin': 'WI',
        'Wyoming': 'WY'
    }

import matplotlib.pyplot as plt

for state in cases:
    state_tidy = state.lower().replace(" ", "-")
    if state_tidy in [
            "american-samoa",
            "guam",
            "diamond-princess",
            "grand-princess",
            "northern-mariana-islands",
            "virgin-islands",
            "district-of-columbia",
            "puerto-rico"]:
        continue

    if state not in us_state_abbrev:
        continue

    abbr = us_state_abbrev[state]

    #if abbr != "MA": continue
    
    pop_vaxeds = round(float(pop_vaxed[state]))

    c = [val for (date, val) in sorted(cases[state].items())]
    d = [val for (date, val) in sorted(deaths[state].items())]

    d_scaled = [x*30 for x in d]

    fig, ax = plt.subplots()
    fig = plt.figure()
    fig.set_size_inches((4, 4))
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    plt.text(0.05, 0.95, abbr,
             horizontalalignment='left',
             verticalalignment='top',
             fontsize=32,
             transform=ax.transAxes)
    ax.plot(c)
    ax.plot([x*100 for x in d])
    plt.savefig("covid-cases-deaths-%s-big.png" % abbr.lower(), bbox_inches=0)
    
    # Now just look at the current wave to see the effect of vaccination
    c = c[-45:]
    d = d[-45:]

    fig, ax = plt.subplots()
    fig = plt.figure()
    fig.set_size_inches((4, 4))
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    plt.text(0.05, 0.95, str(pop_vaxeds) + "% " + abbr,
             horizontalalignment='left',
             verticalalignment='top',
             fontsize=32,
             transform=ax.transAxes)
    ax.plot(c)

    plt.savefig("covid-caseshape-vax-%s-%s-big.png" % (pop_vaxeds-1, abbr.lower()), bbox_inches=0)

    d_pop = [
        x / state_pop[state] for x in d]
    fig, ax = plt.subplots()
    fig = plt.figure()
    fig.set_size_inches((4, 4))
    ax = plt.Axes(fig, [0., 0., 1., 1.],
                  autoscalex_on=True,
                  autoscaley_on=False,
                  ylim=[0,1/100000])
    ax.set_axis_off()
    fig.add_axes(ax)
    plt.text(0.05, 0.95, str(pop_vaxeds) + "% " + abbr,
             horizontalalignment='left',
             verticalalignment='top',
             fontsize=32,
             transform=ax.transAxes)
    ax.plot(d_pop, color="tab:orange")

    plt.savefig("covid-deathabs-vax-%s-%s-big.png" % (pop_vaxeds-1, abbr.lower()), bbox_inches=0)
    
    c_pop = [
        x / state_pop[state] for x in c]
    
    fig, ax = plt.subplots()
    fig = plt.figure()
    fig.set_size_inches((4, 4))
    ax = plt.Axes(fig, [0., 0., 1., 1.],
                  autoscalex_on=True,
                  autoscaley_on=False,
                  ylim=[0,1/1000])
    ax.set_axis_off()
    fig.add_axes(ax)
    plt.text(0.05, 0.95, str(pop_vaxeds) + "% " + abbr,
             horizontalalignment='left',
             verticalalignment='top',
             fontsize=32,
             transform=ax.transAxes)
    ax.plot(c_pop, color="tab:blue")

    plt.savefig("covid-caseabs-vax-%s-%s-big.png" % (pop_vaxeds-1, abbr.lower()), bbox_inches=0)

    fig, ax = plt.subplots()
    fig = plt.figure()
    fig.set_size_inches((4, 4))
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    plt.text(0.05, 0.95, str(pop_vaxeds) + "% " + abbr,
             horizontalalignment='left',
             verticalalignment='top',
             fontsize=32,
             transform=ax.transAxes)
    ax.plot(c)
    ax.plot([x*100 for x in d])

    plt.savefig("covid-casedeathshape-vax-%s-%s-big.png" % (pop_vaxeds-1, abbr.lower()), bbox_inches=0)
    
    plt.close("all")
