from setuptools import setup, find_packages

setup_args = dict(
    name='neat_py',
    version='0.1',
    description='A TAPS conforming transport system building on NEAT',
    license='MIT',
    packages=find_packages(),
    author='Michael Gundersen',
    author_email='michael.nesodden@gmail.com',
    keywords=['TAPS', 'NEAT', 'transport system'],
    url='https://github.com/theagilepadawan/neat_python',
    download_url='https://pypi.org/project/neat_py/'
)

install_requires = [
    'colorama',
]

if __name__ == '__main__':
    setup(**setup_args, install_requires=install_requires)
