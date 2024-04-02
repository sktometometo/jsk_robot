from distutils.core import setup
from catkin_pkg.python_setup import generate_distutils_setup

d = generate_distutils_setup(
    packages=['jsk_spot_lib'],
    package_dir={'': 'python'}
)

setup(**d)
