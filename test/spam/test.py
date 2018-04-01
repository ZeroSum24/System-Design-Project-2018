import unittest

import sys
from pathlib import Path
import os
import shutil as sh
start_dir = Path.cwd()
test_db_dir = next(start_dir.glob('**/test/Databases'))
spam_dirs = tuple(start_dir.glob('**/spam'))
sys.path.extend(tuple(map(str, spam_dirs)))
import spam

class BasicTests(unittest.TestCase):

    @staticmethod
    def setUpClass():
        orig_db = str(spam_dirs[0]/'spam.db')
        if os.path.isfile(orig_db):
            saved_db = str(test_db_dir/'spam.db.orig')
            os.rename(orig_db, saved_db)

    @staticmethod
    def tearDownClass():
        orig_db = str(spam_dirs[0]/'spam.db')
        saved_db = str(test_db_dir/'spam.db.orig')
        if os.path.isfile(saved_db):
            os.rename(saved_db, orig_db)
    
    def setUp(self):
        live_db = str(spam_dirs[0]/'spam.db')
        test_db = str(test_db_dir/'test.db')
        sh.copy(test_db, live_db)
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
        
    def test_access_automode(self):
        rv = self.app.get('/auto_view')
        self.assertTrue('Mail Delivery - Automatic Mode' in rv.data.decode())
        
    def test_access_manualmode(self):
        rv = self.app.get('/view')
        self.assertTrue('Mail Delivery - Manual Mode' in rv.data.decode())
        
    def test_access_notifications(self):
        rv = self.app.get('/notifications')
        self.assertTrue('You have no notifications to solve!' in rv.data.decode())
        
    def test_access_settings(self):
        rv = self.app.get('/settings', follow_redirects=True)
        self.assertTrue(' Welcome to the Administration Page! ' in rv.data.decode())
        
    def test_access_report(self):
        rv = self.app.get('/report')
        self.assertTrue('Report Problem' in rv.data.decode())
        
    def test_access_status(self):
        rv = self.app.get('/status')
        self.assertTrue('Status -- Information' in rv.data.decode())

if __name__ == '__main__':
    unittest.main()
