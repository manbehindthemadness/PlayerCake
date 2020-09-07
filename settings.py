"""
This is our master settings file.
"""

deployment_type = 'writer'
plot_dir = 'plots/'
display = 'localhost:11.0'
screensize = (1024, 600)

theme = 'dark'
themes = {
    'dark': {
        'main': 'black',
        # 'text': '#414141',
        'text': 'white',
        'buttontext': '#06c125',
        'font': 'Helvetica',
        'fontsize': 0.6,
        'scattersize': 0.1,
        'pivotsize': 1,
        'weightsize': 3,
        'plotthickness': 1,
        'plotalpha': 6/10,
        'linewidth': 0.03,
        'entrybackground': 'grey',
    },
    'light': {
        'main': 'white',
        'text': 'black',
        'buttontext': 'black',
        'font': None,
    }
}
defaults = {
    'contact': 50,  # percentage of leg extension to place ground.
    'velocity': 10,  # Implied for sims.
    'resolution': 1.8,  # 180/100 (generally).
    'weightxmin': 50,  # Unit=percentage of velocity.
    'weightxmax': 50,
    'weightymin': 50,
    'weightymax': 50,
    'zlength1': 150,  # Unit=mm (leg length).
    'ztravel1': 70,  # Unit=mm (leg travel).
    'xmax1': 70,  # Unit=degrees.
    'xmin1': -70,
    'ymax1': 70,
    'ymin1': -70,
    'backlash1': 3,  # Unit=degrees.
    'zlength2': 150,
    'ztravel2': 70,
    'xmax2': 70,
    'xmin2': -70,
    'ymax2': 70,
    'ymin2': -70,
    'backlash2': 3,
    'zlength3': 150,
    'ztravel3': 70,
    'xmax3': 70,
    'xmin3': -70,
    'ymax3': 70,
    'ymin3': -70,
    'backlash3': 3,
    'zlength4': 150,
    'ztravel4': 70,
    'xmax4': 70,
    'xmin4': -70,
    'ymax4': 70,
    'ymin4': -70,
    'backlash4': 3,
}
