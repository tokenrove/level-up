from setuptools import setup

setup(name='TracLevelUpGatherer', version='0.1',
      author='Julian Squires', author_email='julian@cipht.net',
      description='Submits bug fix metrics to Level Up.',
      url='http://level-up.appspot.com/',
      license='ad hoc',
      # keywords classifiers long_description
      packages=['level_up'],
      install_requires = ['Trac'],
      entry_points = """
        [trac.plugins]
        level_up = level_up.bug_fix_gatherer
    """)

