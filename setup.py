from setuptools import setup, find_packages
setup(
    name="sync-database",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    py_modules = [ 'sync_database', 'sync_lib' ],

    install_requires=["parallel-ssh", "MergeKeepass"],

    entry_points='''
        [console_scripts]
        sync_database=SyncDatabase.sync_database:cli
    ''',

    # metadata to display on PyPI
    author="Scott Hamilton",
    author_email="sgn.hamilton+pipy@protonmail.com",
    description="Syncs keepass databases to phone, NFS servers and ssh",
    keywords="keepass syncs",
    url="https://github.com/SCOTT-HAMILTON/merge-keepass",
    project_urls={
        "Source Code": "https://github.com/SCOTT-HAMILTON/merge-keepass",
    },
    classifiers=[
        "License :: OSI Approved :: Python Software Foundation License"
    ]
)
