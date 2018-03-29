import unittest

import sys
from pathlib import Path
from itertools import chain
sys.path.extend(tuple(chain(map(str, Path.cwd().glob('spam')), map(str, Path.cwd().glob('spam/spam')))))
import spam

class BasicTests(unittest.TestCase):

    def setUp(self):
        spam.spam.testing = True
        self.app = spam.spam.test_client()

    def tearDown(self):
        pass

    def login(self, uname, password):
        return self.app.post('/', data=dict(
            inputEmail=uname,
            inputPassword=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def test_correct_login(self):
        rv = self.login('admin@admin.com', 'default')
        self.assertTrue('Mail Delivery - Automatic Mode' in rv.data.decode())

    def test_incorrect_login(self):
        rv = self.login('not_even_an_email', 'wrong')
        self.assertTrue('Login - Spam' in rv.data.decode())

    def test_logout(self):
        self.login('admin@admin.com', 'default')
        rv = self.logout()
        self.assertTrue('Login - Spam' in rv.data.decode())

    def test_logout_without_login(self):
        rv = self.logout()
        self.assertTrue('Login - Spam' in rv.data.decode())

if __name__ == '__main__':
    unittest.main()
