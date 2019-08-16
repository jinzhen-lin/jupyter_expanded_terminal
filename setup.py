#encoding: utf-8

from setuptools import setup

with open("README.md") as f:
    readme = f.read()

setup(
    name="jupyter_expanded_terminal",
    version="1.0.2",
    include_package_data=True,
    description="A Jupyter Extension to expand terminal",
    long_description=readme,
    author="Jinzhen Lin",
    author_email="linjinzhen@hotmail.com",
    url="https://github.com/jinzhen-lin/jupyter_expanded_terminal",
    license="BSD",
    python_requires=">=3.5",
    keywords="Jupyter, Notebook, Extension",
    install_requires=["notebook>=4.0"],
    packages=["jupyter_expanded_terminal"],
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities"
    ]
)
