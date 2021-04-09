from setuptools import setup


setup(name='JEOL_eds',
      description='Read binary ".pts" files',
      version='1.5',
      author='Ivo Alxneit',
      author_email='ivo.alxneit@psi.ch',
      packages=['JEOL_eds'],
      install_requires=['numpy',
                        'scipy',
			'matplotlib',
			'h5py',
			'asteval'],
      zip_safe=False)
