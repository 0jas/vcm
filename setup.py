#!/usr/bin/env python3
"""
Setup script for VCM (Version Control Manager)
A Python class to manage Git tags following Semantic Versioning (SemVer) and Gitflow branching model.
"""

from setuptools import setup, find_packages
import os
import io

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(this_directory, "README.md")

def read_long_description():
    """Safely read the README.md file for PyPI long description."""
    if os.path.exists(readme_path):
        with io.open(readme_path, encoding="utf-8") as f:
            return f.read()
    return "A Python class to manage Git tags following SemVer and Gitflow."

long_description = read_long_description()

# Read version from __init__.py or version.py if it exists
def get_version():
    """Extract version string from src/vcm/__init__.py."""
    version_file = os.path.join(this_directory, 'src', 'vcm', '__init__.py')
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            for line in f:
                if line.startswith('__version__'):
                    return line.split('=')[1].strip().strip('"').strip("'")
    return '0.1.0'  # Default version

# Requirements
install_requires = [
    'GitPython>=3.1.45,<4.0.0',
    'packaging>=25.0,<26.0',
    'semver>=3.0.4,<4.0.0',
]

# Development requirements
dev_requires = [
    "pytest>=8.4.2",
    "pytest-cov>=6.10.0",
    "black>=24.10.0",
    "flake8>=7.2.0",
    "mypy>=1.16.0",
    "pre-commit>=4.0.0",
]

# Documentation requirements
docs_requires = [
    "mkdocs>=1.6.1",
    "mkdocs-autorefs>=1.4.3",
    "mkdocs-get-deps>=0.2.0",
    "mkdocs-material>=9.6.20",
    "mkdocs-material-extensions>=1.3.1",
    "mkdocstrings>=0.30.1",
    "mkdocstrings-python>=1.18.2",
]

# --- Setup configuration ---
setup(
    name='vcm',
    version=get_version(),
    author='0jas',
    author_email='0jas.0sv@gmail.com',
    description='A Python class to manage Git tags following Semantic Versioning (SemVer) and Gitflow branching model',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license="MIT",
    url='https://github.com/0jas/vcm',
    project_urls={
        'Bug Reports': 'https://github.com/0jas/vcm/issues',
        'Source': 'https://github.com/0jas/vcm',
        'Documentation': 'https://github.com/0jas/vcm#readme',
    },
    
    # --- Package configuration ---
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    
    # --- Python version requirement ---
    python_requires='>=3.9',
    
    # --- Dependencies ---
    install_requires=install_requires,
    
    # --- Extra dependencies ---
    extras_require={
        'dev': dev_requires,
        'docs': docs_requires,
        'all': dev_requires + docs_requires,
    },
    
    # --- CLI entry point ---
    entry_points={
        'console_scripts': [
            'vcm=vcm.cli:main',
        ],
    },
    
    # --- Classifiers ---
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Version Control',
        'Topic :: Software Development :: Version Control :: Git',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
    ],
    
    # --- Keywords ---
    keywords='git tags semantic versioning semver gitflow version control development',
    
    # --- Include package data ---
    include_package_data=True,
    
    # --- Package data ---
    package_data={
        'vcm': ['*.txt', '*.md', '*.yml', '*.yaml'],
    },
    
    # --- Zip safe ---
    zip_safe=False,
    
    # --- Test suite ---
    test_suite='tests',
    
    # --- Tests require ---
    tests_require=dev_requires,
)
