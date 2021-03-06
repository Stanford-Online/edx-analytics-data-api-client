import json
import re

import httpretty

from analyticsclient.constants import activity_types, data_formats, demographics
from analyticsclient.exceptions import NotFoundError, InvalidRequestError
from analyticsclient.tests import ClientTestCase


class CoursesTests(ClientTestCase):
    def setUp(self):
        super(CoursesTests, self).setUp()
        self.course_id = 'edX/DemoX/Demo_Course'
        self.course = self.client.courses(self.course_id)
        httpretty.enable()

    def tearDown(self):
        super(CoursesTests, self).tearDown()
        httpretty.disable()

    def assertCorrectEnrollmentUrl(self, course, demographic=None):
        """ Verifies that the enrollment URL is correct. """

        uri = self.get_api_url('courses/{0}/enrollment/'.format(course.course_id))
        if demographic:
            uri += '%s/' % demographic

        httpretty.register_uri(httpretty.GET, uri, body='{}')
        course.enrollment(demographic)

        date = '2014-01-01'
        httpretty.reset()
        httpretty.register_uri(httpretty.GET, '{0}?start_date={1}'.format(uri, date), body='{}')
        course.enrollment(demographic, start_date=date)

        httpretty.reset()
        httpretty.register_uri(httpretty.GET, '{0}?end_date={1}'.format(uri, date), body='{}')
        course.enrollment(demographic, end_date=date)

        httpretty.reset()
        httpretty.register_uri(httpretty.GET, '{0}?start_date={1}&end_date={1}'.format(uri, date), body='{}')
        course.enrollment(demographic, start_date=date, end_date=date)

    def assertCorrectActivityUrl(self, course, activity_type=None):
        """ Verifies that the activity URL is correct. """

        uri = self.get_api_url('courses/{0}/activity/'.format(course.course_id))
        if activity_type:
            uri += '?activity_type=%s' % activity_type

        httpretty.register_uri(httpretty.GET, uri, body='{}')
        course.activity(activity_type)

        date = '2014-01-01'
        httpretty.reset()
        httpretty.register_uri(httpretty.GET, '{0}&start_date={1}'.format(uri, date), body='{}')
        course.activity(activity_type, start_date=date)

        httpretty.reset()
        httpretty.register_uri(httpretty.GET, '{0}&end_date={1}'.format(uri, date), body='{}')
        course.activity(activity_type, end_date=date)

        httpretty.reset()
        httpretty.register_uri(httpretty.GET, '{0}&start_date={1}&end_date={1}'.format(uri, date), body='{}')
        course.activity(activity_type, start_date=date, end_date=date)

    @httpretty.activate
    def assertRecentActivityResponseData(self, course, activity_type):
        body = {
            u'course_id': unicode(course.course_id),
            u'interval_start': u'2014-05-24T00:00:00Z',
            u'interval_end': u'2014-06-01T00:00:00Z',
            u'activity_type': unicode(activity_type),
            u'count': 200,
        }

        uri = self.get_api_url('courses/{0}/recent_activity/?activity_type={1}'.format(self.course_id, activity_type))
        httpretty.register_uri(httpretty.GET, uri, body=json.dumps(body))
        self.assertDictEqual(body, self.course.recent_activity(activity_type))

    def test_recent_activity(self):
        self.assertRecentActivityResponseData(self.course, activity_types.ANY)
        self.assertRecentActivityResponseData(self.course, activity_types.ATTEMPTED_PROBLEM)
        self.assertRecentActivityResponseData(self.course, activity_types.PLAYED_VIDEO)
        self.assertRecentActivityResponseData(self.course, activity_types.POSTED_FORUM)

    def test_not_found(self):
        """ Course calls should raise a NotFoundError when provided with an invalid course. """

        course_id = 'not-a-course-id'
        uri = self.get_api_url('courses/{0}/'.format(course_id))
        uri = re.compile(r'^' + re.escape(uri) + r'.*$')
        httpretty.register_uri(httpretty.GET, uri, status=404)

        course = self.client.courses(course_id)
        self.assertRaises(NotFoundError, course.recent_activity, activity_types.ANY)
        self.assertRaises(NotFoundError, course.enrollment, demographics.EDUCATION)

    def test_invalid_parameter(self):
        """ Course calls should raise a InvalidRequestError when parameters are invalid. """

        uri = self.get_api_url('courses/{0}/'.format(self.course_id))
        uri = re.compile(r'^' + re.escape(uri) + r'.*$')
        httpretty.register_uri(httpretty.GET, uri, status=400)

        self.assertRaises(InvalidRequestError, self.course.recent_activity, 'not-a-an-activity-type')
        self.assertRaises(InvalidRequestError, self.course.enrollment, 'not-a-demographic')

    def test_enrollment(self):
        self.assertCorrectEnrollmentUrl(self.course, None)
        self.assertCorrectEnrollmentUrl(self.course, demographics.BIRTH_YEAR)
        self.assertCorrectEnrollmentUrl(self.course, demographics.EDUCATION)
        self.assertCorrectEnrollmentUrl(self.course, demographics.GENDER)
        self.assertCorrectEnrollmentUrl(self.course, demographics.LOCATION)

    def test_activity(self):
        self.assertRaises(InvalidRequestError, self.assertCorrectActivityUrl, self.course, None)
        self.assertCorrectActivityUrl(self.course, activity_types.ANY)
        self.assertCorrectActivityUrl(self.course, activity_types.ATTEMPTED_PROBLEM)
        self.assertCorrectActivityUrl(self.course, activity_types.PLAYED_VIDEO)
        self.assertCorrectActivityUrl(self.course, activity_types.POSTED_FORUM)

    def test_enrollment_data_format(self):
        uri = self.get_api_url('courses/{0}/enrollment/'.format(self.course.course_id))

        httpretty.register_uri(httpretty.GET, uri, body='{}')

        self.course.enrollment()
        self.assertEquals(httpretty.last_request().headers['Accept'], 'application/json')

        httpretty.register_uri(httpretty.GET, uri, body='not-json')
        self.course.enrollment(data_format=data_formats.CSV)
        self.assertEquals(httpretty.last_request().headers['Accept'], 'text/csv')

    @httpretty.activate
    def test_problems(self):

        body = [
            {
                'module_id': 'i4x://a/b/c'
            }
        ]

        uri = self.get_api_url('courses/{0}/problems/'.format(self.course_id))
        httpretty.register_uri(httpretty.GET, uri, body=json.dumps(body))
        self.assertEqual(body, self.course.problems())

    @httpretty.activate
    def test_problems_and_tags(self):

        body = [
            {
                'module_id': 'i4x://a/b/c'
            }
        ]

        uri = self.get_api_url('courses/{0}/problems_and_tags/'.format(self.course_id))
        httpretty.register_uri(httpretty.GET, uri, body=json.dumps(body))
        self.assertEqual(body, self.course.problems_and_tags())

    @httpretty.activate
    def test_reports(self):

        body = {
            "last_modified": "2016-08-12T043411",
            "file_size": 3419,
            "course_id": "Example_Demo_2016-08",
            "expiration_date": "2016-08-12T233704",
            "download_url": "https://bucket.s3.amazonaws.com/foo_bar_1_problem_response.csv?Signature=123&Expires=456",
            "report_name": "problem_response"
        }

        uri = self.get_api_url('courses/{0}/reports/problem_response/'.format(self.course_id))
        httpretty.register_uri(httpretty.GET, uri, body=json.dumps(body))
        self.assertEqual(body, self.course.reports("problem_response"))

    @httpretty.activate
    def test_videos(self):

        body = [
            {
                'pipeline_video_id': '0fac49ba',
                'encoded_module_id': 'i4x-a-b-c',
                'duration': 600,
                'segment_length': 5,
                'start_views': 50,
                'end_views': 1,
                'created': '2015-01-01T00:01:00'
            }
        ]

        uri = self.get_api_url('courses/{0}/videos/'.format(self.course_id))
        httpretty.register_uri(httpretty.GET, uri, body=json.dumps(body))
        self.assertEqual(body, self.course.videos())
