# from setuptools import setup
#
# setup(
#     name='spam',
#     packages=['spam'],
#     include_package_data=True,
#     install_requires=[
#         'flask',
#     ],
# )
from spam import spam, db
from spam.models import Staff,Location, Problem

@spam.shell_context_processor
def make_shell_context():
    return {'db': db, 'Staff': Staff, 'Location': Location}
