from setuptools import setup

setup(
    name='spam',
    packages=['spam'],
    include_package_data=True,
    install_requires=[
        'flask',
    ],
)
