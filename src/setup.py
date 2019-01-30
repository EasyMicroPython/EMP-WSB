from distutils.core import setup

setup(
    name='emp-wsb',
    version='1.2',
    packages=['emp_wsb'],
    include_package_data=True,
    license='MIT License',
    description='Easy MicroPython WebSocket-SerialPort-Bridge',
    url='https://github.com/EasyMicroPython/EMP-WSB',
    author='Singein',
    author_email='Singein@outlook.com',
    platforms='Linux,Unix,Windows',
    keywords='EasyMicroPython EMP 1ZLAB EMP-WSB WebSocket-SerialPort-Bridge',
    entry_points={
        'console_scripts': [
            'empwsb = emp_wsb.cli:cli'
        ]
    }
)
