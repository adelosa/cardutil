from setuptools import setup, find_packages

readme = open('README.rst', 'r').read()

setup(name='cardutil',
      packages=find_packages(),
      version='0.1.1',
      license='MIT',
      description='Library and toolset for working with payment card messages and files',
      long_description=readme,
      long_description_content_type='text/x-rst',
      author='Anthony Delosa',
      author_email='adelosa@gmail.com',
      url='https://bitbucket.org/hoganman/cardutil',
      install_requires=[],
      extras_require={
        'docs': ['sphinx']
      },
      classifiers=[
            'Development Status :: 5 - Production/Stable',
            # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
      ])
