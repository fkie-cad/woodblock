from setuptools import setup, find_packages

setup(
    name='woodblock',
    version='0.1.0',
    license='MIT',
    author='Fraunhofer FKIE',
    author_email='martin.lambertz@fkie.fraunhofer.de',
    url='https://github.com/fkie-cad/woodblock',
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
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ]
)
