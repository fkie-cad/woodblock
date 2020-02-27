from setuptools import setup, find_packages


def long_description():
    with open('README.md') as fh:
        desc = fh.read()
    desc = desc.replace('documentation/docs/',
                        'https://raw.githubusercontent.com/fkie-cad/woodblock/master/documentation/docs/')
    return desc


setup(
    name='woodblock',
    version='0.1.7',
    license='MIT',
    author='Fraunhofer FKIE',
    author_email='martin.lambertz@fkie.fraunhofer.de',
    url='https://github.com/fkie-cad/woodblock/',
    packages=find_packages(),
    install_requires=[
        'click',
        'multimethod',
        'numpy',
    ],
    entry_points={
        'console_scripts': [
            'woodblock = woodblock.__main__:main'
        ]
    },
    description='A framework to generate file carving test data',
    long_description=long_description(),
    long_description_content_type='text/markdown',
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    project_urls={
        'Documentation': 'https://fkie-cad.github.io/woodblock/',
        'Source': 'https://github.com/fkie-cad/woodblock/',
        'Tracker': 'https://github.com/fkie-cad/woodblock/issues',
    },
    python_requires='>3.6',
)
