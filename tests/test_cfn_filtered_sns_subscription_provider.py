import unittest
import uuid
from cfn_filtered_sns_subscription_provider import FilteredSNSSubscriptionProvider
from main import handler
import boto3

region = boto3.session.Session().region_name
account_id = (boto3.client('sts')).get_caller_identity()['Account']

test_sns_topic = 'cfn-filtered-sns-subscription-provider-testing'
sqs_arn = 'arn:aws:sqs:{}:{}:{}'.format(region, account_id, test_sns_topic)

test_filter = {
    'store': [
        'example_corp'
    ],
    'event': [
        'order_cancelled',
        'order_placed'
    ]
}

test_filter2 = {
    'store': [
        'other_corp'
    ],
    'event': [
        'order_cancelled',
        'order_placed'
    ]
}


class CfnSecretProviderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sns = boto3.client('sns')
        cls.sqs = boto3.client('sqs')
        response = cls.sns.create_topic(Name=test_sns_topic)
        cls.topic_arn = response['TopicArn']
        response = cls.sqs.create_queue(QueueName=test_sns_topic)
        cls.sqs_queue = response['QueueUrl']

    @classmethod
    def tearDownClass(cls):
        cls.sns.delete_topic(TopicArn=cls.topic_arn)
        cls.sqs.delete_queue(QueueUrl=cls.sqs_queue)

    def test_defaults(self):
        request = Request('Create', self.topic_arn, sqs_arn, 'sqs', test_filter)
        r = FilteredSNSSubscriptionProvider()
        r.set_request(request, {})
        self.assertTrue(r.is_valid_request())
        self.assertEqual(r.get('TopicArn'), request['ResourceProperties']['TopicArn'])
        self.assertEqual(r.get('Endpoint'), request['ResourceProperties']['Endpoint'])
        self.assertEqual(r.get('Protocol'), request['ResourceProperties']['Protocol'])
        self.assertEqual(r.get('FilterPolicy'), request['ResourceProperties']['FilterPolicy'])

    def test_create_delete(self):
        # create a subscription
        request = Request('Create', self.topic_arn, sqs_arn, 'sqs', test_filter)
        response = handler(request, {})
        self.assertTrue(response['Status'], 'SUCCESS')
        self.assertIn('PhysicalResourceId', response)
        physical_resource_id = response['PhysicalResourceId']
        self.assertIsInstance(physical_resource_id, str)

        # delete the subscription
        request = Request('Delete', self.topic_arn, sqs_arn, 'sqs', test_filter, physical_resource_id)
        response = handler(request, {})
        assert response['Status'] == 'SUCCESS', response['Reason']


class Request(dict):

    def __init__(self, request_type, arn, endpoint, protocol, filter_policy, physical_resource_id=None):
        self.update({
            'RequestType': request_type,
            'ResponseURL': 'https://httpbin.org/put',
            'StackId': 'arn:aws:cloudformation:us-west-2:EXAMPLE/stack-name/guid',
            'RequestId': 'request-%s' % uuid.uuid4(),
            'ResourceType': 'Custom::FilteredSNSSubscription',
            'LogicalResourceId': 'MySNSSubscription',
            'ResourceProperties': {
                'TopicArn': arn,
                'Endpoint': endpoint,
                'Protocol': protocol,
                'FilterPolicy': filter_policy
            }})
        self['PhysicalResourceId'] = physical_resource_id if physical_resource_id is not None else str(uuid.uuid4())


if __name__ == '__main__':
    unittest.main()
