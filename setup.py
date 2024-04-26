from setuptools import setup, find_packages

from pathlib import Path
# Read the contents of README.md
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()


setup(
    name='EditableFlask',
    version='1.0',
    description='Addon to Library named flask which helps to edit html content in running app0',
    long_description=long_description,
    long_description_content_type='text/markdown',  # Specify the content type as Markdown
    url='',
    author='Mahir Shah',
    author_email='mahir.shah.sd@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
    ],
    keywords='editable_flask',
    packages=find_packages(),
    package_data={
        'EditableFlask': ['templates/*.html', 'assets/**'],
    },
    install_requires=['Flask', 'flask_login']
)
