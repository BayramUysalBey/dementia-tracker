from datetime import datetime, timezone, timedelta
import unittest
from app import create_app, db
from app.models import Caregiver, SymptomLog
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'




class CaregiverModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        c = Caregiver(caregiver_name='susan', email='susan@example.com')
        c.set_password('cat')
        self.assertFalse(c.check_password('dog'))
        self.assertTrue(c.check_password('cat'))

    def test_avatar(self):
        c = Caregiver(caregiver_name='john', email='john@example.com')
        self.assertEqual(c.avatar(128), ('https://www.gravatar.com/avatar/'
                                         'd4c74594d841139328695756648b6bd6'
                                         '?d=identicon&s=128'))

    def test_follow(self):
        c1 = Caregiver(caregiver_name='john', email='john@example.com')
        c2 = Caregiver(caregiver_name='susan', email='susan@example.com')
        db.session.add(c1)
        db.session.add(c2)
        db.session.commit()
        following = db.session.scalars(c1.following.select()).all()
        followers = db.session.scalars(c2.followers.select()).all()
        self.assertEqual(following, [])
        self.assertEqual(followers, [])

        c1.follow(c2)
        db.session.commit()
        self.assertTrue(c1.is_following(c2))
        self.assertEqual(c1.following_count(), 1)
        self.assertEqual(c2.followers_count(), 1)
        c1_following = db.session.scalars(c1.following.select()).all()
        c2_followers = db.session.scalars(c2.followers.select()).all()
        self.assertEqual(c1_following[0].caregiver_name, 'susan')
        self.assertEqual(c2_followers[0].caregiver_name, 'john')

        c1.unfollow(c2)
        db.session.commit()
        self.assertFalse(c1.is_following(c2))
        self.assertEqual(c1.following_count(), 0)
        self.assertEqual(c2.followers_count(), 0)

    def test_follow_symtomlogs(self):
        # create four caregivers
        c1 = Caregiver(caregiver_name='john', email='john@example.com')
        c2 = Caregiver(caregiver_name='susan', email='susan@example.com')
        c3 = Caregiver(caregiver_name='mary', email='mary@example.com')
        c4 = Caregiver(caregiver_name='david', email='david@example.com')
        db.session.add_all([c1, c2, c3, c4])

        # create four symptomlogs
        now = datetime.now(timezone.utc)
        s1 = SymptomLog(diagnosis="symptomlog from john", observer=c1,
                  timestamp=now + timedelta(seconds=1))
        s2 = SymptomLog(diagnosis="symptomlog from susan", observer=c2,
                  timestamp=now + timedelta(seconds=4))
        s3 = SymptomLog(diagnosis="symptomlog from mary", observer=c3,
                  timestamp=now + timedelta(seconds=3))
        s4 = SymptomLog(diagnosis="symptomlog from david", observer=c4,
                  timestamp=now + timedelta(seconds=2))
        db.session.add_all([s1, s2, s3, s4])
        db.session.commit()

        # setup the followers
        c1.follow(c2)  # john follows susan
        c1.follow(c4)  # john follows david
        c2.follow(c3)  # susan follows mary
        c3.follow(c4)  # mary follows david
        db.session.commit()

        # check the following posts of each user
        f1 = db.session.scalars(c1.following_symptomlogs()).all()
        f2 = db.session.scalars(c2.following_symptomlogs()).all()
        f3 = db.session.scalars(c3.following_symptomlogs()).all()
        f4 = db.session.scalars(c4.following_symptomlogs()).all()
        self.assertEqual(f1, [s2, s4, s1])
        self.assertEqual(f2, [s2, s3])
        self.assertEqual(f3, [s3, s4])
        self.assertEqual(f4, [s4])


if __name__ == '__main__':
    unittest.main(verbosity=2)