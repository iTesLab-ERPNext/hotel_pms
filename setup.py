from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="hotel_pms",
    version="1.0.0",
    description="Hotel Property Management System for Frappe v15",
    author="Hotel PMS",
    author_email="info@hotelpms.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
