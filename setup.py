from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="hotel_pms",
    version="1.0.0",
    description="Hotel Property Management System for ERPNext",
    author="iTesLab",
    author_email="info@iteslab.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
